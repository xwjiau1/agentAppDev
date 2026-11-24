package dev.agent.rag;

import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Supplier;

import static dev.agent.rag.Contracts.*;

final class QdrantIndex implements ChunkIndex {
    private static final List<String> PAYLOAD_FIELDS = List.of("documentId", "source", "title", "page", "chunkIndex", "text");

    private final RestClient client;
    private final String collectionPath;

    QdrantIndex(RestClient client, String collection) {
        this.client = client;
        this.collectionPath = "/collections/" + collection;
    }

    private record DenseConfig(int size, String distance) {}
    private record SparseConfig(String modifier) {}
    private record Parameters(Map<String, DenseConfig> vectors, Map<String, SparseConfig> sparse_vectors) {}
    private record Config(Parameters params, Manifest metadata) {}
    private record CollectionInfo(Config config) {}
    private record CollectionResponse(CollectionInfo result) {}
    private record Count(long count) {}
    private record CountResponse(Count result) {}
    private record Point(UUID id, Map<String, Object> vector, Source payload) {}
    private record ScoredPoint(UUID id, Double score, Source payload) {}
    private record QueryResult(List<ScoredPoint> points) {}
    private record QueryResponse(QueryResult result) {}

    @Override
    public Manifest manifest() {
        return call(() -> {
            CollectionResponse response;
            try {
                response = client.get().uri(collectionPath).retrieve().body(CollectionResponse.class);
            } catch (RestClientResponseException exception) {
                if (exception.getStatusCode().value() == 404) {
                    return null;
                }
                throw exception;
            }
            if (response == null || response.result() == null || response.result().config() == null) {
                throw new RagFailure(502, "Qdrant returned an invalid collection response");
            }
            Config config = response.result().config();
            Parameters params = config.params();
            if (params == null || !Map.of("dense", new DenseConfig(DIMENSION, "Cosine")).equals(params.vectors())
                    || params.sparse_vectors() == null || !params.sparse_vectors().keySet().equals(java.util.Set.of("sparse"))
                    || !List.of("none", "").contains(java.util.Objects.toString(params.sparse_vectors().get("sparse").modifier(), ""))) {
                throw new RagFailure(503, "Qdrant collection has incompatible named vectors");
            }
            Manifest manifest = config.metadata();
            if (manifest == null || manifest.corpusFingerprint() == null || manifest.modelSignature() == null
                    || manifest.chunkStrategy() == null || manifest.state() == null
                    || !List.of("building", "ready").contains(manifest.state())) {
                throw new RagFailure(503, "Qdrant collection has an invalid manifest");
            }
            return manifest;
        });
    }

    @Override
    public void create(Manifest manifest) {
        call(() -> client.put().uri(collectionPath).body(Map.of(
                "vectors", Map.of("dense", new DenseConfig(DIMENSION, "Cosine")),
                "sparse_vectors", Map.of("sparse", Map.of()), "metadata", manifest)).retrieve().toBodilessEntity());
    }

    @Override
    public void ensureDocumentIndex() {
        call(() -> client.put().uri(collectionPath + "/index?wait=true")
                .body(Map.of("field_name", "documentId", "field_schema", "keyword")).retrieve().toBodilessEntity());
    }

    @Override
    public long count() {
        return call(() -> {
            CountResponse response = client.post().uri(collectionPath + "/points/count")
                    .body(Map.of("exact", true)).retrieve().body(CountResponse.class);
            if (response == null || response.result() == null) {
                throw new RagFailure(502, "Qdrant returned no point count");
            }
            return response.result().count();
        });
    }

    @Override
    public void upsert(List<EmbeddedChunk> chunks) {
        List<Point> points = chunks.stream().map(row -> {
            Embedding embedding = row.embedding();
            Map<String, Object> vectors = new HashMap<>();
            vectors.put("dense", embedding.dense());
            if (!embedding.sparse().empty()) {
                vectors.put("sparse", embedding.sparse());
            }
            return new Point(row.chunk().id(), vectors, row.chunk().source());
        }).toList();
        call(() -> client.put().uri(collectionPath + "/points?wait=true")
                .body(Map.of("points", points)).retrieve().toBodilessEntity());
    }

    @Override
    public void publish(Manifest manifest) {
        call(() -> client.patch().uri(collectionPath).body(Map.of("metadata", manifest)).retrieve().toBodilessEntity());
    }

    @Override
    public List<Match> search(Embedding query, List<String> documentIds, Mode mode, int limit) {
        if (query.sparse().empty()) {
            if (mode == Mode.SPARSE) {
                return List.of();
            }
            mode = Mode.DENSE;
        }
        Map<String, Object> filter = documentIds.isEmpty() ? Map.of() : Map.of("must", List.of(
                Map.of("key", "documentId", "match", Map.of("any", documentIds))));
        Map<String, Object> request = switch (mode) {
            case HYBRID -> new HashMap<>(Map.of("prefetch", List.of(
                    nearest("dense", query.dense(), filter, PREFETCH_LIMIT),
                    nearest("sparse", query.sparse(), filter, PREFETCH_LIMIT)), "query", Map.of("fusion", "rrf"), "limit", limit));
            case DENSE -> nearest("dense", query.dense(), filter, limit);
            case SPARSE -> nearest("sparse", query.sparse(), filter, limit);
        };
        request.put("with_payload", PAYLOAD_FIELDS);
        request.put("with_vector", false);
        String scoreType = switch (mode) {
            case HYBRID -> "rrf";
            case DENSE -> "dense";
            case SPARSE -> "sparse";
        };
        return call(() -> {
            QueryResponse response = client.post().uri(collectionPath + "/points/query")
                    .body(request).retrieve().body(QueryResponse.class);
            if (response == null || response.result() == null || response.result().points() == null) {
                throw new RagFailure(502, "Qdrant returned an invalid search response");
            }
            return response.result().points().stream().map(point -> match(point, scoreType)).toList();
        });
    }

    private Map<String, Object> nearest(String using, Object vector, Map<String, Object> filter, int limit) {
        Map<String, Object> request = new HashMap<>(Map.of("query", vector, "using", using, "limit", limit));
        if (!filter.isEmpty()) {
            request.put("filter", filter);
        }
        return request;
    }

    private Match match(ScoredPoint point, String scoreType) {
        Source source = point.payload();
        if (point.id() == null || point.score() == null || !Double.isFinite(point.score()) || source == null
                || source.documentId() == null || source.source() == null || source.title() == null || source.text() == null) {
            throw new RagFailure(502, "Qdrant returned an invalid hit payload");
        }
        return new Match(point.id(), source, point.score(), scoreType);
    }

    private <T> T call(Supplier<T> operation) {
        try {
            return operation.get();
        } catch (RestClientException failure) {
            throw new RagFailure(503, "Qdrant request failed", failure);
        }
    }
}

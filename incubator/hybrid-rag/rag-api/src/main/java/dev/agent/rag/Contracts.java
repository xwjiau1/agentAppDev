package dev.agent.rag;

import java.util.HashSet;
import java.util.List;
import java.util.UUID;

final class Contracts {
    static final int DIMENSION = 1024;
    static final int CANDIDATE_LIMIT = 20;
    static final int PREFETCH_LIMIT = 30;

    private Contracts() {}

    record Source(String documentId, String source, String title, Integer page, int chunkIndex, String text) {}
    record Chunk(UUID id, Source source) {}
    record Sparse(List<Integer> indices, List<Float> values) {
        Sparse {
            if (indices == null || values == null || indices.size() != values.size()
                    || new HashSet<>(indices).size() != indices.size()) {
                throw new IllegalArgumentException("Invalid sparse vector shape");
            }
            int previous = -1;
            for (int i = 0; i < indices.size(); i++) {
                if (indices.get(i) == null || indices.get(i) <= previous || values.get(i) == null
                        || !Float.isFinite(values.get(i))) {
                    throw new IllegalArgumentException("Invalid sparse vector entry");
                }
                previous = indices.get(i);
            }
        }

        boolean empty() {
            return indices.isEmpty();
        }
    }

    record Embedding(List<Float> dense, Sparse sparse) {
        Embedding {
            if (dense == null || dense.size() != DIMENSION
                    || dense.stream().anyMatch(value -> value == null || !Float.isFinite(value)) || sparse == null) {
                throw new IllegalArgumentException("Invalid embedding shape");
            }
        }
    }

    record EmbeddedChunk(Chunk chunk, Embedding embedding) {}
    record Match(UUID id, Source source, double score, String scoreType) {}
    record Candidate(UUID chunkId, String text) {}
    record ScoredCandidate(UUID chunkId, Double score) {}
    record Manifest(String corpusFingerprint, String modelSignature, String chunkStrategy, String state) {
        Manifest ready() {
            return new Manifest(corpusFingerprint, modelSignature, chunkStrategy, "ready");
        }

        boolean compatibleWith(Manifest other) {
            return corpusFingerprint.equals(other.corpusFingerprint)
                    && modelSignature.equals(other.modelSignature) && chunkStrategy.equals(other.chunkStrategy);
        }
    }

    enum Mode { DENSE, SPARSE, HYBRID }

    interface EncoderClient {
        String signature();
        List<Embedding> encode(List<String> texts, String expectedSignature, String requestId);
    }

    interface RerankerClient {
        List<ScoredCandidate> score(String query, List<Candidate> candidates, String requestId);
    }

    interface ChunkIndex {
        Manifest manifest();
        void create(Manifest manifest);
        void ensureDocumentIndex();
        long count();
        void upsert(List<EmbeddedChunk> chunks);
        void publish(Manifest manifest);
        List<Match> search(Embedding query, List<String> documentIds, Mode mode, int limit);
    }
}

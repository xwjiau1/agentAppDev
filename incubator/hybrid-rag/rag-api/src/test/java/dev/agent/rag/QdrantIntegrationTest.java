package dev.agent.rag;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.web.client.RestClient;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import static dev.agent.rag.Contracts.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@EnabledIfEnvironmentVariable(named = "TEST_QDRANT_URL", matches = "https?://.+")
class QdrantIntegrationTest {
    @TempDir Path directory;

    @Test
    void retriesPartialImportAndQueriesNamedVectorsWithSharedDocumentFilter() throws Exception {
        RestClient client = RestClient.create(System.getenv("TEST_QDRANT_URL"));
        String collection = "test_" + UUID.randomUUID();
        var index = new QdrantIndex(client, collection);
        Path corpus = Files.createDirectory(directory.resolve("corpus"));
        for (int i = 0; i < 6; i++) {
            Files.writeString(corpus.resolve("a" + i + ".txt"), "Noise document " + i);
        }
        CorpusReaderTest.writeRepeatedTextPdf(corpus.resolve("policy.pdf"));
        Path target = Files.writeString(corpus.resolve("z.txt"), "P-8472 relevant evidence");
        var sparse = new Sparse(List.of(8472), List.of(1F));
        var embedding = new Embedding(Collections.nCopies(DIMENSION, 1F), sparse);
        var requests = new AtomicInteger();
        EncoderClient encoder = new EncoderClient() {
            @Override
            public String signature() {
                return "test-model";
            }

            @Override
            public List<Embedding> encode(List<String> texts, String signature, String requestId) {
                if (requests.incrementAndGet() == 2) {
                    throw new RagFailure(503, "Simulated encoder outage");
                }
                return Collections.nCopies(texts.size(), embedding);
            }
        };
        var ingest = new IngestService(new CorpusReader(), encoder, index, corpus, directory.resolve("ingest.lock"));

        try {
            assertThatThrownBy(ingest::run).hasMessageContaining("Simulated encoder outage");
            assertThat(index.manifest().state()).isEqualTo("building");
            assertThat(index.count()).isEqualTo(8);

            ingest.run();
            ingest.run();
            assertThat(index.manifest().state()).isEqualTo("ready");
            assertThat(index.count()).isEqualTo(9);
            assertThat(requests.get()).isEqualTo(4);
            var hit = index.search(embedding, List.of(), Mode.HYBRID, 20).stream()
                    .filter(result -> result.source().source().equals("z.txt")).findFirst().orElseThrow();
            for (var mode : Mode.values()) {
                var filtered = index.search(embedding, List.of(hit.source().documentId()), mode, 20);
                assertThat(filtered).singleElement().satisfies(candidate -> {
                    assertThat(candidate.id()).isEqualTo(hit.id());
                    assertThat(candidate.source().text()).isEqualTo("P-8472 relevant evidence");
                });
            }
            assertThat(index.search(embedding, List.of("unknown-document"), Mode.HYBRID, 20)).isEmpty();
            String pdfId = UUID.nameUUIDFromBytes("policy.pdf".getBytes(StandardCharsets.UTF_8)).toString();
            var pdfHits = index.search(embedding, List.of(pdfId), Mode.HYBRID, 20);
            assertThat(pdfHits).extracting(Match::id).doesNotHaveDuplicates();
            assertThat(pdfHits).extracting(row -> row.source().page()).containsExactlyInAnyOrder(1, 2);
            assertThat(pdfHits).allSatisfy(row -> assertThat(row.source().text()).isEqualTo("Identical evidence"));
            var denseOnly = new Embedding(embedding.dense(), new Sparse(List.of(), List.of()));
            assertThat(index.search(denseOnly, List.of(hit.source().documentId()), Mode.HYBRID, 20))
                    .singleElement().satisfies(candidate -> assertThat(candidate.scoreType()).isEqualTo("dense"));

            Files.writeString(target, "Changed corpus");
            assertThatThrownBy(ingest::run).hasMessageContaining("snapshot or model changed");
            assertThat(index.count()).isEqualTo(9);
        } finally {
            client.delete().uri("/collections/" + collection).retrieve().toBodilessEntity();
        }
    }
}

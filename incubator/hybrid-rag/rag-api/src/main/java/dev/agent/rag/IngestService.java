package dev.agent.rag;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.UUID;

import static dev.agent.rag.Contracts.*;

record IngestService(CorpusReader reader, EncoderClient encoder, ChunkIndex index, Path corpus, Path lockFile) {
    private static final Logger LOG = LoggerFactory.getLogger(IngestService.class);
    private static final int BATCH_SIZE = 8;

    void run() throws IOException {
        Files.createDirectories(lockFile.toAbsolutePath().getParent());
        try (var channel = FileChannel.open(lockFile, StandardOpenOption.CREATE, StandardOpenOption.WRITE);
             var lock = channel.tryLock()) {
            if (lock == null) {
                throw new IOException("Another importer holds the ingest lock");
            }
            ingest();
        }
    }

    private void ingest() throws IOException {
        var snapshot = reader.read(corpus);
        String signature = encoder.signature();
        var expected = new Manifest(snapshot.fingerprint(), signature, CorpusReader.STRATEGY, "building");
        var existing = index.manifest();
        if (existing == null) {
            index.create(expected);
        } else if (!expected.compatibleWith(existing)) {
            throw new RagFailure(503, "Collection snapshot or model changed. Create a new collection to rebuild.");
        } else if (existing.state().equals("ready")) {
            checkCount(snapshot.chunks().size());
            LOG.info("Snapshot already ready fingerprint={} points={}", expected.corpusFingerprint(), snapshot.chunks().size());
            return;
        }

        index.ensureDocumentIndex();
        var chunks = snapshot.chunks();
        String requestId = UUID.randomUUID().toString();
        for (int start = 0; start < chunks.size(); start += BATCH_SIZE) {
            var batch = chunks.subList(start, Math.min(start + BATCH_SIZE, chunks.size()));
            var embeddings = encoder.encode(batch.stream().map(chunk -> chunk.source().text()).toList(), signature, requestId);
            var points = new ArrayList<EmbeddedChunk>(batch.size());
            for (int i = 0; i < batch.size(); i++) {
                points.add(new EmbeddedChunk(batch.get(i), embeddings.get(i)));
            }
            index.upsert(points);
        }
        checkCount(chunks.size());
        index.publish(expected.ready());
        LOG.info("Published snapshot fingerprint={} points={}", expected.corpusFingerprint(), chunks.size());
    }

    private void checkCount(int expected) {
        long count = index.count();
        if (count != expected) {
            throw new RagFailure(503, "Point count mismatch: expected " + expected + ", found " + count);
        }
    }
}

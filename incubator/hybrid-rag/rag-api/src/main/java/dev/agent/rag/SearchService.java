package dev.agent.rag;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.UUID;

import static dev.agent.rag.Contracts.*;

record SearchService(EncoderClient encoder, ChunkIndex index, RerankerClient reranker, boolean rerankEnabled, int contextBudget) {
    private static final Logger LOG = LoggerFactory.getLogger(SearchService.class);

    record Hit(UUID chunkId, String documentId, String source, String title, Integer page, int chunkIndex,
               String text, double score, String scoreType) {
        static Hit from(Match match) {
            Source source = match.source();
            return new Hit(match.id(), source.documentId(), source.source(), source.title(), source.page(),
                    source.chunkIndex(), source.text(), match.score(), match.scoreType());
        }
    }

    record Citation(int number, UUID chunkId, String documentId, String source, String title, Integer page, int chunkIndex) {}
    record Result(String requestId, List<Hit> hits, List<Citation> citations, String context, boolean rerankDegraded) {}

    String readySignature() {
        var manifest = index.manifest();
        if (manifest == null || !manifest.state().equals("ready")) {
            throw new RagFailure(503, "Search index is not ready");
        }
        if (!manifest.chunkStrategy().equals(CorpusReader.STRATEGY) || !manifest.modelSignature().equals(encoder.signature())) {
            throw new RagFailure(503, "Search index is incompatible with the running encoder or chunk strategy");
        }
        return manifest.modelSignature();
    }

    Result search(String query, int topK, List<String> documentIds, Mode mode, boolean useReranker, String requestId) {
        long start = System.nanoTime();
        String signature = readySignature();
        Embedding embedding = encoder.encode(List.of(query), signature, requestId).getFirst();
        var unique = new LinkedHashMap<UUID, Match>();
        for (Match candidate : index.search(embedding, documentIds, mode, CANDIDATE_LIMIT)) {
            unique.putIfAbsent(candidate.id(), candidate);
        }
        List<Match> ranked = List.copyOf(unique.values());
        boolean degraded = false;
        if (rerankEnabled && useReranker && !ranked.isEmpty()) {
            try {
                ranked = reorder(query, ranked, requestId);
            } catch (RagFailure failure) {
                LOG.warn("requestId={} rerankFallback={}", requestId, failure.getMessage());
                degraded = true;
            }
        }
        var hits = ranked.stream().limit(topK).map(Hit::from).toList();
        LOG.info("requestId={} mode={} candidates={} hits={} elapsedMs={}", requestId, mode, ranked.size(), hits.size(),
                (System.nanoTime() - start) / 1_000_000);
        return context(hits, requestId, degraded);
    }

    private List<Match> reorder(String query, List<Match> candidates, String requestId) {
        var inputs = candidates.stream().map(hit -> new Candidate(hit.id(), hit.source().text())).toList();
        var response = reranker.score(query, inputs, requestId);
        var scores = new HashMap<UUID, Double>();
        if (response == null || response.size() != inputs.size()) {
            throw new RagFailure(502, "Reranker returned the wrong candidate count");
        }
        for (var item : response) {
            if (item == null || item.chunkId() == null || item.score() == null || !Double.isFinite(item.score())
                    || scores.putIfAbsent(item.chunkId(), item.score()) != null) {
                throw new RagFailure(502, "Reranker returned invalid candidate scores");
            }
        }
        if (inputs.stream().anyMatch(item -> !scores.containsKey(item.chunkId()))) {
            throw new RagFailure(502, "Reranker returned unexpected candidate IDs");
        }
        return candidates.stream().map(hit -> new Match(hit.id(), hit.source(), scores.get(hit.id()), "reranker"))
                .sorted(Comparator.comparingDouble(Match::score).reversed()).toList();
    }

    private Result context(List<Hit> hits, String requestId, boolean degraded) {
        var citations = new ArrayList<Citation>();
        var text = new StringBuilder();
        for (var hit : hits) {
            int number = citations.size() + 1;
            String location = hit.page() == null ? ", 切片 " + hit.chunkIndex() : ", 第 " + hit.page() + " 页";
            String block = (text.isEmpty() ? "" : "\n\n") + "[" + number + "] " + hit.source() + location + "\n" + hit.text();
            if (text.length() + block.length() > contextBudget) {
                continue;
            }
            text.append(block);
            citations.add(new Citation(number, hit.chunkId(), hit.documentId(), hit.source(), hit.title(), hit.page(), hit.chunkIndex()));
        }
        return new Result(requestId, hits, List.copyOf(citations), text.toString(), degraded);
    }
}

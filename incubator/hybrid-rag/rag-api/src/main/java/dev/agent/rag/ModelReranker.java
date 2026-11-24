package dev.agent.rag;

import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.List;
import java.util.Map;

import static dev.agent.rag.Contracts.*;

record ModelReranker(RestClient client) implements RerankerClient {
    private record Scores(List<ScoredCandidate> items) {}

    @Override
    public List<ScoredCandidate> score(String query, List<Candidate> candidates, String requestId) {
        try {
            Scores response = client.post().uri("/rerank").header("X-Request-ID", requestId)
                    .body(Map.of("query", query, "candidates", candidates)).retrieve().body(Scores.class);
            return response == null ? null : response.items();
        } catch (RestClientException failure) {
            throw new RagFailure(503, "Reranker request failed", failure);
        }
    }
}

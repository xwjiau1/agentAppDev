package dev.agent.rag;

import org.junit.jupiter.api.Test;

import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static dev.agent.rag.Contracts.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class SearchServiceTest {
    private final EncoderClient encoder = mock(EncoderClient.class);
    private final ChunkIndex index = mock(ChunkIndex.class);
    private final RerankerClient reranker = mock(RerankerClient.class);

    private SearchService service(int budget) {
        when(encoder.signature()).thenReturn("test-model");
        when(index.manifest()).thenReturn(new Manifest("corpus", "test-model", CorpusReader.STRATEGY, "ready"));
        when(encoder.encode(anyList(), eq("test-model"), eq("request"))).thenReturn(List.of(
                new Embedding(Collections.nCopies(1024, 1F), new Sparse(List.of(2), List.of(1F)))));
        return new SearchService(encoder, index, reranker, true, budget);
    }

    @Test
    void rerankingPreservesOriginalPdfPageAndStableTieOrder() {
        Match first = pdfHit(1);
        Match second = pdfHit(2);
        Match third = pdfHit(3);
        when(index.search(any(), eq(List.of("doc")), eq(Mode.HYBRID), eq(20))).thenReturn(List.of(first, second, third, first));
        when(reranker.score(eq("policy"), anyList(), eq("request"))).thenReturn(List.of(
                new ScoredCandidate(third.id(), 2D), new ScoredCandidate(first.id(), 1D), new ScoredCandidate(second.id(), 2D)));

        var result = service(4000).search("policy", 2, List.of("doc"), Mode.HYBRID, true, "request");

        assertThat(result.hits()).extracting(SearchService.Hit::chunkId).containsExactly(second.id(), third.id());
        assertThat(result.citations()).extracting(SearchService.Citation::page).containsExactly(2, 3);
        assertThat(result.context()).contains("[1] policy.pdf, 第 2 页", "[2] policy.pdf, 第 3 页");
        assertThat(result.rerankDegraded()).isFalse();
    }

    @Test
    void invalidRerankFallsBackAndOnlyCitesCompleteContextBlocks() {
        Match first = pdfHit(1);
        Match second = pdfHit(2);
        when(index.search(any(), anyList(), eq(Mode.HYBRID), eq(20))).thenReturn(List.of(first, second));
        when(reranker.score(anyString(), anyList(), anyString())).thenReturn(List.of(
                new ScoredCandidate(first.id(), 3D), new ScoredCandidate(first.id(), 2D)));

        var result = service(55).search("policy", 2, List.of(), Mode.HYBRID, true, "request");

        assertThat(result.rerankDegraded()).isTrue();
        assertThat(result.hits()).extracting(SearchService.Hit::scoreType).containsExactly("rrf", "rrf");
        assertThat(result.citations()).extracting(SearchService.Citation::page).containsExactly(1);
        assertThat(result.context()).doesNotContain("第 2 页");
    }

    @Test
    void incompatibleModelCannotQueryPublishedIndex() {
        var service = service(4000);
        when(encoder.signature()).thenReturn("different-model");
        assertThatThrownBy(() -> service.search("policy", 2, List.of(), Mode.HYBRID, true, "request"))
                .isInstanceOf(RagFailure.class).hasMessageContaining("incompatible");
        verify(index, never()).search(any(), anyList(), any(), anyInt());
    }

    private Match pdfHit(int page) {
        return new Match(UUID.randomUUID(), new Source("doc", "policy.pdf", "policy.pdf", page, 0, "Policy evidence"), 0.5, "rrf");
    }
}

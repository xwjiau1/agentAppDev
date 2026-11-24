package dev.agent.rag;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Path;

import static dev.agent.rag.Contracts.Chunk;
import static org.assertj.core.api.Assertions.assertThat;

class CorpusReaderTest {
    @TempDir Path directory;

    @Test
    void identicalTextOnTwoPagesHasDistinctStablePoints() throws IOException {
        writeRepeatedTextPdf(directory.resolve("policy.pdf"));
        var reader = new CorpusReader();
        var snapshot = reader.read(directory);

        assertThat(snapshot).isEqualTo(reader.read(directory));
        assertThat(snapshot.chunks()).extracting(Chunk::id).doesNotHaveDuplicates();
        assertThat(snapshot.chunks()).extracting(chunk -> chunk.source().text())
                .containsExactly("Identical evidence", "Identical evidence");
        assertThat(snapshot.chunks()).extracting(chunk -> chunk.source().page()).containsExactly(1, 2);
        assertThat(snapshot.chunks()).extracting(chunk -> chunk.source().chunkIndex()).containsExactly(0, 0);
    }

    static void writeRepeatedTextPdf(Path path) throws IOException {
        try (var pdf = new PDDocument()) {
            for (int i = 0; i < 2; i++) {
                var page = new PDPage();
                pdf.addPage(page);
                try (var text = new PDPageContentStream(pdf, page)) {
                    text.beginText();
                    text.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA), 12);
                    text.newLineAtOffset(50, 750);
                    text.showText("Identical evidence");
                    text.endText();
                }
            }
            pdf.save(path.toFile());
        }
    }
}

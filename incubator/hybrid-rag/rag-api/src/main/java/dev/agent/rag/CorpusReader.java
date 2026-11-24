package dev.agent.rag;

import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.splitter.DocumentSplitters;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

import static dev.agent.rag.Contracts.*;

final class CorpusReader {
    static final String STRATEGY = "langchain4j-1.8.0-recursive-utf16-480-64-pdfbox-3.0.6-per-page-v1";
    private static final int MAX_FILES = 1000;
    private static final int MAX_CHUNKS = 20_000;
    private static final int MAX_FILE_BYTES = 16 * 1024 * 1024;
    private static final int MAX_PAGES = 2000;
    private static final Set<String> SUPPORTED = Set.of("txt", "md", "pdf");

    private final dev.langchain4j.data.document.DocumentSplitter splitter = DocumentSplitters.recursive(480, 64);

    record Snapshot(String fingerprint, List<Chunk> chunks) {}

    Snapshot read(Path root) throws IOException {
        List<Path> files;
        try (var paths = Files.walk(root)) {
            files = paths.filter(path -> !Files.isSymbolicLink(path) && Files.isRegularFile(path))
                    .filter(path -> SUPPORTED.contains(extension(path))).limit(MAX_FILES + 1L).toList();
        }
        if (files.isEmpty() || files.size() > MAX_FILES) {
            throw new IOException("Corpus must contain between 1 and " + MAX_FILES + " supported files");
        }
        files = files.stream().sorted(Comparator.comparing(path -> source(root, path))).toList();
        MessageDigest fingerprint = digest();
        List<Chunk> chunks = new ArrayList<>();
        for (Path file : files) {
            String source = source(root, file);
            byte[] bytes;
            try (var input = Files.newInputStream(file)) {
                bytes = input.readNBytes(MAX_FILE_BYTES + 1);
            }
            if (bytes.length > MAX_FILE_BYTES) {
                throw new IOException("Corpus file exceeds size limit: " + source);
            }
            byte[] contentHash = digest().digest(bytes);
            fingerprint.update(source.getBytes(StandardCharsets.UTF_8));
            fingerprint.update((byte) 0);
            fingerprint.update(contentHash);
            String documentId = stableId(source).toString();
            String title = file.getFileName().toString();
            int previousSize = chunks.size();
            if (extension(file).equals("pdf")) {
                try (var document = Loader.loadPDF(bytes)) {
                    if (document.getNumberOfPages() > MAX_PAGES) {
                        throw new IOException("PDF exceeds page limit: " + source);
                    }
                    var stripper = new PDFTextStripper();
                    stripper.setSortByPosition(true);
                    for (int page = 1; page <= document.getNumberOfPages(); page++) {
                        stripper.setStartPage(page);
                        stripper.setEndPage(page);
                        split(chunks, documentId, source, title, page, contentHash, stripper.getText(document));
                    }
                }
            } else {
                String text = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(bytes)).toString();
                split(chunks, documentId, source, title, null, contentHash, text.replaceFirst("^\uFEFF", ""));
            }
            if (previousSize == chunks.size()) {
                throw new IOException("No extractable text: " + source);
            }
        }
        return new Snapshot(HexFormat.of().formatHex(fingerprint.digest()), List.copyOf(chunks));
    }

    private void split(List<Chunk> chunks, String documentId, String source, String title, Integer page,
                       byte[] contentHash, String text) throws IOException {
        if (text.isBlank()) {
            return;
        }
        var segments = splitter.split(Document.from(text));
        if (chunks.size() + segments.size() > MAX_CHUNKS) {
            throw new IOException("Corpus exceeds chunk limit of " + MAX_CHUNKS);
        }
        for (int i = 0; i < segments.size(); i++) {
            UUID id = stableId(source + "\0" + HexFormat.of().formatHex(contentHash) + "\0" + page + "\0" + i + "\0" + STRATEGY);
            chunks.add(new Chunk(id, new Source(documentId, source, title, page, i, segments.get(i).text())));
        }
    }

    private static MessageDigest digest() {
        try {
            return MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException failure) {
            throw new IllegalStateException(failure);
        }
    }

    private static UUID stableId(String value) {
        return UUID.nameUUIDFromBytes(value.getBytes(StandardCharsets.UTF_8));
    }

    private static String source(Path root, Path file) {
        return root.relativize(file).toString().replace(file.getFileSystem().getSeparator(), "/");
    }

    private static String extension(Path path) {
        String name = path.getFileName().toString();
        int dot = name.lastIndexOf('.');
        return dot < 0 ? "" : name.substring(dot + 1).toLowerCase(Locale.ROOT);
    }
}

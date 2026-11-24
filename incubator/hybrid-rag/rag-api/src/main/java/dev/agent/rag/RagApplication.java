package dev.agent.rag;

import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.Arrays;

@SpringBootApplication
@EnableConfigurationProperties(RagSettings.class)
public class RagApplication {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(RagApplication.class);
        if (args.length > 0 && args[0].equals("ingest")) {
            app.setWebApplicationType(WebApplicationType.NONE);
            try (var context = app.run(Arrays.copyOfRange(args, 1, args.length))) {
                context.getBean(IngestService.class).run();
            } catch (RagFailure | IOException failure) {
                LoggerFactory.getLogger(RagApplication.class).error("Import failed: {}", failure.getMessage());
                System.exit(1);
            }
        } else {
            app.run(args);
        }
    }

    @Configuration(proxyBeanMethods = false)
    static class Wiring {
        @Bean
        SearchService searchService(RagSettings settings, RestClient.Builder builder) {
            return new SearchService(new ModelEncoder(client(builder, settings.encoderUrl(), settings.queryTimeout())),
                    index(settings, builder, settings.queryTimeout()),
                    new ModelReranker(client(builder, settings.rerankerUrl(), settings.rerankTimeout())),
                    settings.rerankEnabled(), settings.contextBudget());
        }

        @Bean
        IngestService ingestService(RagSettings settings, RestClient.Builder builder) {
            return new IngestService(new CorpusReader(),
                    new ModelEncoder(client(builder, settings.encoderUrl(), settings.ingestTimeout())),
                    index(settings, builder, settings.ingestTimeout()), settings.corpus(), settings.ingestLock());
        }

        private QdrantIndex index(RagSettings settings, RestClient.Builder builder, Duration timeout) {
            return new QdrantIndex(client(builder, settings.qdrantUrl(), timeout), settings.collection());
        }

        private RestClient client(RestClient.Builder builder, String base, Duration timeout) {
            var factory = new JdkClientHttpRequestFactory(HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(3)).version(HttpClient.Version.HTTP_1_1).build());
            factory.setReadTimeout(timeout);
            return builder.clone().baseUrl(base).requestFactory(factory).build();
        }
    }
}

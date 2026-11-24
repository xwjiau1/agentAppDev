FROM maven:3.9.11-eclipse-temurin-21@sha256:6fdc855a6ed81d288ca7ca37ac6ff5e9308b612485c0801d70b25a858c83d237 AS build
WORKDIR /build
COPY pom.xml mvnw ./
COPY .mvn ./.mvn
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 sh ./mvnw -B -ntp verify

FROM eclipse-temurin:21.0.9_10-jre-jammy@sha256:cc11c035bb25cc709d7b1e3f43cbff15d69e06e2dba23eec431b64627d27e705
WORKDIR /app
COPY --from=build /build/target/rag-api-0.1.0.jar ./rag-api.jar
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=50", "-jar", "/app/rag-api.jar"]

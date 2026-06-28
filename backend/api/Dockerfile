FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY backend/pom.xml backend/pom.xml
COPY backend/api/pom.xml backend/api/pom.xml
COPY backend/api/src backend/api/src
WORKDIR /workspace/backend
RUN mvn -q -pl api -am -DskipTests package
RUN find api/target -maxdepth 1 -name 'insureflow-api-*.jar' ! -name '*.original' -exec cp {} /tmp/insureflow-api.jar \;

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /tmp/insureflow-api.jar /app/insureflow-api.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/insureflow-api.jar"]

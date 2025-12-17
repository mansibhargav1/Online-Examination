FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app

# Copy everything
COPY . .
RUN mvn -q clean package -DskipTests -U
# 🟢 FIX 1: Clear Maven cache to avoid corrupted downloads
RUN rm -rf /root/.m2/repository

# 🟢 FIX 2: Increase timeout + retry attempts (prevents download failure)
RUN mvn -q clean package -DskipTests \
    -Dmaven.wagon.httpconnectionManager.ttlSeconds=120 \
    -Dmaven.wagon.http.retryHandler.count=5

# -----------------------------
# Runtime Image
# -----------------------------
FROM eclipse-temurin:17-jdk
WORKDIR /app

COPY --from=build /app/target/*.jar /app/backend.jar

EXPOSE 8081
ENTRYPOINT ["java", "-jar", "/app/backend.jar"]


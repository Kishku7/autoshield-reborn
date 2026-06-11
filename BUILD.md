# Building the 26.1.2 universal jar

Two per-loader projects, both JDK 25, mojmap-native (no Architectury):
- `fabric/`   -> `./gradlew build` -> build/libs/autoshield-reborn-1.0.0+26.1.2.jar
- `neoforge/` -> `./gradlew build` -> build/libs/autoshield-reborn-1.0.0+26.1.2-neoforge.jar

Merge into one universal jar with Forgix 2.0 (https://github.com/PacifistMC/Forgix):

    java -cp <Forgix-shadow.jar> io.github.pacifistmc.forgix.Forgix mergeJars \
      --output autoshield-reborn-1.0.0+26.1.2.jar \
      --fabric fabric/build/libs/autoshield-reborn-1.0.0+26.1.2.jar \
      --neoforge neoforge/build/libs/autoshield-reborn-1.0.0+26.1.2-neoforge.jar

Forgix mutates its inputs, so feed it copies. The merged jar runs on both Fabric and NeoForge.

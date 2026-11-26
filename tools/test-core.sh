#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
L=${GRADLE_LIB:-/opt/gradle/lib}; out=$(mktemp -d)
CP=$(ls $L/kotlin-{compiler-embeddable,stdlib,script-runtime,reflect,daemon-embeddable}-*.jar $L/trove4j-*.jar $L/kotlinx-coroutines-core-jvm-*.jar $L/annotations-*.jar | paste -sd:)
TCP="$(ls $L/kotlin-stdlib-2*.jar):$L/junit-4.13.2.jar:$L/hamcrest-core-1.3.jar"
java -cp "$CP" org.jetbrains.kotlin.cli.jvm.K2JVMCompiler -no-stdlib -no-reflect -classpath "$TCP" -d "$out" core/src
classes=$(cd "$out" && find . -name '*Test.class' | sed 's|^\./||; s|\.class$||; s|/|.|g')
java -cp "$out:$TCP" org.junit.runner.JUnitCore $classes

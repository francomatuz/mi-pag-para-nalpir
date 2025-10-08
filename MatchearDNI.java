import java.io.*;
import java.text.Normalizer;
import java.util.*;

public class MatchearDNI {

    // Clase para almacenar datos de una persona con DNI
    static class PersonaConDNI {
        String cod;
        String nombreyapellido;
        String dni;

        PersonaConDNI(String cod, String nombreyapellido, String dni) {
            this.cod = cod;
            this.nombreyapellido = nombreyapellido;
            this.dni = dni;
        }
    }

    // Clase para almacenar resultados del matcheo
    static class Resultado {
        String cuenta;
        String nombre;
        String dni;
        String cod;
        String similitud;

        Resultado(String cuenta, String nombre, String dni, String cod, String similitud) {
            this.cuenta = cuenta;
            this.nombre = nombre;
            this.dni = dni;
            this.cod = cod;
            this.similitud = similitud;
        }
    }

    // Normaliza texto: sin acentos, mayúsculas, sin espacios extras
    public static String normalizarTexto(String texto) {
        if (texto == null || texto.trim().isEmpty()) {
            return "";
        }

        // Quitar acentos
        String normalized = Normalizer.normalize(texto, Normalizer.Form.NFD);
        normalized = normalized.replaceAll("\\p{M}", "");

        // Mayúsculas y quitar espacios extras
        normalized = normalized.toUpperCase().trim().replaceAll("\\s+", " ");

        return normalized;
    }

    // Quita ceros a la izquierda de la cuenta
    public static String normalizarCuenta(String cuenta) {
        return cuenta.replaceFirst("^0+(?!$)", "");
    }

    // Calcula similitud entre dos cadenas usando Levenshtein simplificado
    public static double similitudTexto(String s1, String s2) {
        if (s1 == null) s1 = "";
        if (s2 == null) s2 = "";

        int maxLen = Math.max(s1.length(), s2.length());
        if (maxLen == 0) return 1.0;

        int distance = levenshteinDistance(s1, s2);
        return 1.0 - ((double) distance / maxLen);
    }

    // Distancia de Levenshtein
    private static int levenshteinDistance(String s1, String s2) {
        if (s1 == null || s1.isEmpty()) return s2 == null ? 0 : s2.length();
        if (s2 == null || s2.isEmpty()) return s1.length();

        int len1 = s1.length();
        int len2 = s2.length();

        int[][] dp = new int[len1 + 1][len2 + 1];

        for (int i = 0; i <= len1; i++) {
            dp[i][0] = i;
        }
        for (int j = 0; j <= len2; j++) {
            dp[0][j] = j;
        }

        for (int i = 1; i <= len1; i++) {
            for (int j = 1; j <= len2; j++) {
                int cost = (s1.charAt(i - 1) == s2.charAt(j - 1)) ? 0 : 1;
                dp[i][j] = Math.min(Math.min(
                    dp[i - 1][j] + 1,      // eliminación
                    dp[i][j - 1] + 1),     // inserción
                    dp[i - 1][j - 1] + cost); // sustitución
            }
        }

        return dp[len1][len2];
    }

    // Calcula similitud entre dos nombres
    public static double similitudNombre(String nombre1, String nombre2) {
        String n1 = normalizarTexto(nombre1);
        String n2 = normalizarTexto(nombre2);

        // Similitud directa
        double similitudDirecta = similitudTexto(n1, n2);

        // También verificar cobertura de palabras
        Set<String> palabras1 = new HashSet<>(Arrays.asList(n1.split(" ")));
        Set<String> palabras2 = new HashSet<>(Arrays.asList(n2.split(" ")));

        double cobertura = 0.0;
        if (!palabras1.isEmpty() && !palabras2.isEmpty()) {
            Set<String> comunes = new HashSet<>(palabras1);
            comunes.retainAll(palabras2);
            cobertura = (double) comunes.size() / Math.max(palabras1.size(), palabras2.size());
        }

        // Retornar el máximo
        return Math.max(similitudDirecta, cobertura);
    }

    // Parsea una línea CSV considerando comillas y punto y coma
    public static String[] parsearLineaCSV(String linea) {
        List<String> campos = new ArrayList<>();
        boolean dentroComillas = false;
        StringBuilder campoActual = new StringBuilder();

        for (int i = 0; i < linea.length(); i++) {
            char c = linea.charAt(i);

            if (c == '"') {
                dentroComillas = !dentroComillas;
            } else if (c == ';' && !dentroComillas) {
                campos.add(campoActual.toString());
                campoActual = new StringBuilder();
            } else {
                campoActual.append(c);
            }
        }
        campos.add(campoActual.toString());

        return campos.toArray(new String[0]);
    }

    public static void main(String[] args) {
        System.out.println("=== INICIANDO PROCESO DE MATCHEO ===\n");

        // Rutas de archivos (ajustar según ubicación)
        String archivoConDNI = "con_dni.txt";
        String archivoSinDNI = "sin_dni.txt";
        String archivoResultado = "resultado_matcheado.txt";

        try {
            // Paso 1: Cargar archivo con DNI
            System.out.println("Cargando archivo con DNI (2.7M registros)...");
            Map<String, PersonaConDNI> dniDict = new HashMap<>();

            BufferedReader brConDNI = new BufferedReader(
                new InputStreamReader(new FileInputStream(archivoConDNI), "ISO-8859-1")
            );

            String linea = brConDNI.readLine(); // Saltar header
            int contadorCarga = 0;

            while ((linea = brConDNI.readLine()) != null) {
                String[] campos = parsearLineaCSV(linea);

                if (campos.length >= 5) {
                    String cuenta = campos[0];
                    String cod = campos[2];
                    String nombreyapellido = campos[3];
                    String dni = campos[4];

                    String cuentaNorm = normalizarCuenta(cuenta);
                    dniDict.put(cuentaNorm, new PersonaConDNI(cod, nombreyapellido, dni));

                    contadorCarga++;
                    if (contadorCarga % 100000 == 0) {
                        System.out.println("  Cargados " + contadorCarga + " registros...");
                    }
                }
            }
            brConDNI.close();

            System.out.println("Cargados " + dniDict.size() + " registros con DNI");
            System.out.println("\nProcesando archivo sin DNI (400k registros)...\n");

            // Paso 2: Procesar archivo sin DNI
            BufferedReader brSinDNI = new BufferedReader(
                new InputStreamReader(new FileInputStream(archivoSinDNI), "ISO-8859-1")
            );

            List<Resultado> resultados = new ArrayList<>();
            int matcheados = 0;
            int noMatcheados = 0;
            int rechazadosPorNombre = 0;

            brSinDNI.readLine(); // Saltar header
            int idx = 0;

            while ((linea = brSinDNI.readLine()) != null) {
                idx++;
                String[] campos = parsearLineaCSV(linea);

                if (campos.length >= 2) {
                    String cuenta = campos[0];
                    String nombreSinDNI = campos[1];

                    String cuentaNorm = normalizarCuenta(cuenta);

                    // Buscar por cuenta
                    if (dniDict.containsKey(cuentaNorm)) {
                        PersonaConDNI persona = dniDict.get(cuentaNorm);

                        // Verificar similitud de nombres
                        double similitud = similitudNombre(nombreSinDNI, persona.nombreyapellido);

                        if (similitud >= 0.51) {
                            resultados.add(new Resultado(
                                cuenta,
                                nombreSinDNI,
                                persona.dni,
                                persona.cod,
                                String.format("%.2f%%", similitud * 100)
                            ));
                            matcheados++;
                        } else {
                            resultados.add(new Resultado(
                                cuenta,
                                nombreSinDNI,
                                "RECHAZADO_NOMBRE_DIFERENTE",
                                "",
                                String.format("%.2f%%", similitud * 100)
                            ));
                            rechazadosPorNombre++;
                        }
                    } else {
                        resultados.add(new Resultado(
                            cuenta,
                            nombreSinDNI,
                            "NO_ENCONTRADO",
                            "",
                            "N/A"
                        ));
                        noMatcheados++;
                    }

                    if (idx % 10000 == 0) {
                        System.out.println("Procesados " + idx + " registros... " +
                            "(Matcheados: " + matcheados +
                            ", No encontrados: " + noMatcheados +
                            ", Rechazados: " + rechazadosPorNombre + ")");
                    }
                }
            }
            brSinDNI.close();

            // Paso 3: Guardar resultados
            System.out.println("\nTotal procesados: " + idx);
            System.out.println("Matcheados exitosamente: " + matcheados);
            System.out.println("Rechazados por nombre diferente: " + rechazadosPorNombre);
            System.out.println("No encontrados: " + noMatcheados);

            System.out.println("\nGuardando resultados...");

            BufferedWriter bw = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream(archivoResultado), "ISO-8859-1")
            );

            // Escribir header
            bw.write("\"cuenta\";\"nombre\";\"dni\";\"cod\";\"similitud\"\n");

            // Escribir resultados
            for (Resultado r : resultados) {
                bw.write(String.format("\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"\n",
                    r.cuenta, r.nombre, r.dni, r.cod, r.similitud));
            }

            bw.close();

            // Guardar rechazados en archivo separado
            System.out.println("\nGuardando rechazados por nombre diferente...");
            BufferedWriter bwRechazados = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("rechazados_por_nombre.txt"), "ISO-8859-1")
            );

            bwRechazados.write("\"cuenta\";\"nombre_sin_dni\";\"nombre_con_dni\";\"dni_encontrado\";\"similitud\"\n");

            for (Resultado r : resultados) {
                if (r.dni.equals("RECHAZADO_NOMBRE_DIFERENTE")) {
                    // Buscar el nombre que se encontró con DNI
                    String cuentaNorm = normalizarCuenta(r.cuenta);
                    PersonaConDNI persona = dniDict.get(cuentaNorm);
                    String nombreConDNI = persona != null ? persona.nombreyapellido : "N/A";
                    String dniEncontrado = persona != null ? persona.dni : "N/A";

                    bwRechazados.write(String.format("\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"\n",
                        r.cuenta, r.nombre, nombreConDNI, dniEncontrado, r.similitud));
                }
            }

            bwRechazados.close();
            System.out.println("Archivo de rechazados guardado como 'rechazados_por_nombre.txt'");

            // Guardar no encontrados en archivo separado
            System.out.println("\nGuardando no encontrados por cuenta...");
            BufferedWriter bwNoEncontrados = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("no_encontrados_por_cuenta.txt"), "ISO-8859-1")
            );

            bwNoEncontrados.write("\"cuenta\";\"nombre\"\n");

            for (Resultado r : resultados) {
                if (r.dni.equals("NO_ENCONTRADO")) {
                    bwNoEncontrados.write(String.format("\"%s\";\"%s\"\n",
                        r.cuenta, r.nombre));
                }
            }

            bwNoEncontrados.close();
            System.out.println("Archivo de no encontrados guardado como 'no_encontrados_por_cuenta.txt'");

            System.out.println("\n¡Proceso completado! Archivo guardado como 'resultado_matcheado.txt'");
            System.out.println("\nColumnas del archivo resultado:");
            System.out.println("- cuenta: número de cuenta original");
            System.out.println("- nombre: nombre del archivo sin_dni");
            System.out.println("- dni: DNI encontrado (o 'NO_ENCONTRADO' / 'RECHAZADO_NOMBRE_DIFERENTE')");
            System.out.println("- cod: código encontrado");
            System.out.println("- similitud: porcentaje de similitud entre nombres");

        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}

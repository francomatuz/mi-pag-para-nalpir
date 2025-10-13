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

    // Genera una contraseña aleatoria de 9 caracteres (letras y números)
    public static String generarPasswordAleatoria() {
        String caracteres = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder password = new StringBuilder();
        Random random = new Random();

        for (int i = 0; i < 9; i++) {
            password.append(caracteres.charAt(random.nextInt(caracteres.length())));
        }

        return password.toString();
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
            // int rechazadosPorNombre = 0;  // COMENTADO: Ya no usamos rechazados
            Map<String, Integer> contadorPorCod = new HashMap<>();  // Para contar por COD

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

                        // NUEVO: Agregar TODOS los encontrados con cualquier similitud
                        resultados.add(new Resultado(
                            cuenta,
                            nombreSinDNI,
                            persona.dni,
                            persona.cod,
                            String.format("%.2f%%", similitud * 100)
                        ));
                        matcheados++;

                        // Contar por COD
                        contadorPorCod.put(persona.cod, contadorPorCod.getOrDefault(persona.cod, 0) + 1);

                        /* COMENTADO: Lógica anterior con umbral de 51%
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
                        */
                    } else {
                        // NUEVO: Generar contraseña aleatoria para los no encontrados
                        String passwordAleatoria = generarPasswordAleatoria();
                        resultados.add(new Resultado(
                            cuenta,
                            nombreSinDNI,
                            passwordAleatoria,
                            "",
                            "NO_ENCONTRADO"
                        ));
                        noMatcheados++;
                    }

                    if (idx % 10000 == 0) {
                        System.out.println("Procesados " + idx + " registros... " +
                            "(Matcheados: " + matcheados +
                            ", No encontrados: " + noMatcheados + ")");
                    }
                }
            }
            brSinDNI.close();

            // Paso 3: Mostrar estadísticas por COD
            System.out.println("\n=== ESTADÍSTICAS POR COD ===");
            List<Map.Entry<String, Integer>> listaOrdenada = new ArrayList<>(contadorPorCod.entrySet());
            listaOrdenada.sort((a, b) -> a.getKey().compareTo(b.getKey())); // Ordenar por COD

            for (Map.Entry<String, Integer> entry : listaOrdenada) {
                System.out.println("COD " + entry.getKey() + ": " + entry.getValue() + " personas");
            }

            // Paso 4: Guardar resultados
            System.out.println("\n=== RESUMEN TOTAL ===");
            System.out.println("Total procesados: " + idx);
            System.out.println("Matcheados exitosamente: " + matcheados);
            // System.out.println("Rechazados por nombre diferente: " + rechazadosPorNombre);  // COMENTADO
            System.out.println("No encontrados (con password generada): " + noMatcheados);

            System.out.println("\nGuardando resultados...");

            // NUEVO: Archivo con TODOS los encontrados (cualquier similitud)
            BufferedWriter bwTodos = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("todos_encontrados.txt"), "ISO-8859-1")
            );

            // NUEVO: Archivo solo con los de 51% o más
            BufferedWriter bw51Plus = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("encontrados_51_o_mas.txt"), "ISO-8859-1")
            );

            String headerTodos = "\"cuenta\";\"nombre\";\"dni\";\"cod\"\n";
            String header51Plus = "\"cuenta\";\"nombre\";\"dni\";\"cod\";\"similitud\"\n";
            bwTodos.write(headerTodos);
            bw51Plus.write(header51Plus);

            // Escribir resultados de encontrados
            for (Resultado r : resultados) {
                if (!r.similitud.equals("NO_ENCONTRADO")) {
                    // Archivo TODOS: sin similitud
                    String lineaTodos = String.format("\"%s\";\"%s\";\"%s\";\"%s\"\n",
                        r.cuenta, r.nombre, r.dni, r.cod);
                    bwTodos.write(lineaTodos);

                    // Escribir en archivo de 51% o más (con similitud)
                    double similitud = Double.parseDouble(r.similitud.replace("%", "").replace(",", "."));
                    if (similitud >= 51.0) {
                        String linea51Plus = String.format("\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"\n",
                            r.cuenta, r.nombre, r.dni, r.cod, r.similitud);
                        bw51Plus.write(linea51Plus);
                    }
                }
            }

            bwTodos.close();
            bw51Plus.close();

            System.out.println("Archivos de encontrados guardados:");
            System.out.println("  - todos_encontrados.txt (todas las similitudes)");
            System.out.println("  - encontrados_51_o_mas.txt (solo >= 51%)");

            // NUEVO: Generar archivo input.txt con solo DNI (sin ceros adelante)
            System.out.println("\nGenerando archivo input.txt con DNIs...");
            BufferedWriter bwInput = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("input.txt"), "ISO-8859-1")
            );

            for (Resultado r : resultados) {
                if (!r.similitud.equals("NO_ENCONTRADO")) {
                    // Quitar ceros adelante del DNI
                    String dniSinCeros = r.dni.replaceFirst("^0+(?!$)", "");
                    bwInput.write(dniSinCeros + "\n");
                }
            }

            bwInput.close();
            System.out.println("Archivo input.txt generado con DNIs línea por línea (sin ceros adelante)");

            /* COMENTADO: Código anterior de rechazados por rangos
            // Guardar rechazados en archivo separado Y agrupados por rangos
            System.out.println("\nGuardando rechazados por nombre diferente...");

            // Archivo general de rechazados
            BufferedWriter bwRechazados = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("rechazados_por_nombre.txt"), "ISO-8859-1")
            );

            // Archivos por rangos de similitud
            BufferedWriter bw50 = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("rechazados_50_porciento.txt"), "ISO-8859-1")
            );
            BufferedWriter bw49_30 = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("rechazados_49_a_30_porciento.txt"), "ISO-8859-1")
            );
            BufferedWriter bw29_10 = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("rechazados_29_a_10_porciento.txt"), "ISO-8859-1")
            );
            BufferedWriter bw09_0 = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("rechazados_09_a_0_porciento.txt"), "ISO-8859-1")
            );

            String header = "\"cuenta\";\"nombre_sin_dni\";\"nombre_con_dni\";\"dni_encontrado\";\"similitud\"\n";
            bwRechazados.write(header);
            bw50.write(header);
            bw49_30.write(header);
            bw29_10.write(header);
            bw09_0.write(header);

            for (Resultado r : resultados) {
                if (r.dni.equals("RECHAZADO_NOMBRE_DIFERENTE")) {
                    // Buscar el nombre que se encontró con DNI
                    String cuentaNorm = normalizarCuenta(r.cuenta);
                    PersonaConDNI persona = dniDict.get(cuentaNorm);
                    String nombreConDNI = persona != null ? persona.nombreyapellido : "N/A";
                    String dniEncontrado = persona != null ? persona.dni : "N/A";

                    String lineaRechazado = String.format("\"%s\";\"%s\";\"%s\";\"%s\";\"%s\"\n",
                        r.cuenta, r.nombre, nombreConDNI, dniEncontrado, r.similitud);

                    // Escribir en archivo general
                    bwRechazados.write(lineaRechazado);

                    // Determinar rango y escribir en archivo correspondiente
                    double similitud = Double.parseDouble(r.similitud.replace("%", "").replace(",", "."));

                    if (similitud == 50.0) {
                        bw50.write(lineaRechazado);
                    } else if (similitud >= 30.0 && similitud <= 49.0) {
                        bw49_30.write(lineaRechazado);
                    } else if (similitud >= 10.0 && similitud <= 29.0) {
                        bw29_10.write(lineaRechazado);
                    } else if (similitud >= 0.0 && similitud <= 9.0) {
                        bw09_0.write(lineaRechazado);
                    }
                }
            }

            bwRechazados.close();
            bw50.close();
            bw49_30.close();
            bw29_10.close();
            bw09_0.close();

            System.out.println("Archivos de rechazados guardados:");
            System.out.println("  - rechazados_por_nombre.txt (todos)");
            System.out.println("  - rechazados_50_porciento.txt");
            System.out.println("  - rechazados_49_a_30_porciento.txt");
            System.out.println("  - rechazados_29_a_10_porciento.txt");
            System.out.println("  - rechazados_09_a_0_porciento.txt");

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
            */

            // NUEVO: Guardar no encontrados con contraseña generada
            System.out.println("\nGuardando no encontrados con contraseñas...");
            BufferedWriter bwNoEncontrados = new BufferedWriter(
                new OutputStreamWriter(new FileOutputStream("no_encontrados_con_password.txt"), "ISO-8859-1")
            );

            bwNoEncontrados.write("\"cuenta\";\"nombre\";\"password\"\n");

            for (Resultado r : resultados) {
                if (r.similitud.equals("NO_ENCONTRADO")) {
                    bwNoEncontrados.write(String.format("\"%s\";\"%s\";\"%s\"\n",
                        r.cuenta, r.nombre, r.dni));  // El dni contiene la password generada
                }
            }

            bwNoEncontrados.close();
            System.out.println("Archivo de no encontrados guardado como 'no_encontrados_con_password.txt'");

            System.out.println("\n¡Proceso completado!");
            System.out.println("\nArchivos generados:");
            System.out.println("- todos_encontrados.txt: Todos los matcheos (cualquier similitud)");
            System.out.println("- encontrados_51_o_mas.txt: Solo matcheos con 51% o más de similitud");
            System.out.println("- no_encontrados_con_password.txt: Cuentas no encontradas con contraseñas generadas");

        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}

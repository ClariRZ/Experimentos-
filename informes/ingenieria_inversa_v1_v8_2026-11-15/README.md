# Ingeniería inversa de Historia 2019: v1–v8

[**Abrir el archivo HTML**](index.html). GitHub muestra el código: descargar el archivo y abrirlo en un navegador para ver el informe. Funciona sin conexión; las fuentes enlazadas requieren internet.

El documento reconstruye preguntas, decisiones, resultados, fortalezas y límites de las ocho versiones. Incluye fichas desplegables, 37 brazos v4–v8 filtrables, cierre económico v8, intervalos, explicación de variables, fallos operativos y aplicación a la segunda competencia. No suma ganancias de diseños incompatibles ni reemplaza reglas antiguas por criterios posteriores.

**Conclusión:** relativos y tendencia mostraron señales útiles; T4 es la alternativa más consistente del cierre v8, pero no cumple el criterio ajustado. La evidencia no prueba que las variables estén mal construidas ni permite declarar una receta universalmente superior. B0 como referencia y T4 exploratorio son recomendaciones posteriores, no promociones originales.

## Alcance y reproducción documental

- `index.html`: informe autónomo; filtros, detalles y estilos de impresión.
- `evidencia.json`: números de las tablas, sin datos individuales.
- `fuentes_sha256.json`: fuentes locales y sus hashes.
- `VERIFICACION.json`: comprobaciones realizadas y sus límites.
- `QA_HTML.json`: controles en navegador de escritorio y móvil.
- `referencias/`: CSV público de la revisión de Ezequiel, fijado a commit; no es su estado actual.
- `construir.py`: reconstruye HTML y datos derivados desde fuentes versionadas.
- `MANIFIESTO_SHA256.json`: identidad de los archivos de este entregable.

Desde la raíz del repositorio:

```bash
python3 informes/ingenieria_inversa_v1_v8_2026-11-15/construir.py
```

La construcción usa biblioteca estándar; no entrena, no modifica fuentes y no accede a la nube. Se reejecutaron el extractor agregado de v4–v6, el verificador de v7 y el verificador público de v8. No se recalcularon predicciones privadas ni se reentrenaron modelos en esta revisión. El manifiesto histórico v6 conserva una discrepancia conocida en README.

Las consignas de Ale y la tutoría provienen del texto compartido por Clara en la conversación. La limpieza de v8 se registra según la salida compartida, no una inspección nueva de la VM. La copia privada v8 fue verificada en Cloud Shell según el recibo; no está en el ZIP público recibido localmente.

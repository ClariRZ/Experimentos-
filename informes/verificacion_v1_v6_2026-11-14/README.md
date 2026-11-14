# Verificación de respaldos v1 y v6 — 14/11/2026

## Comprobado localmente

- `HISTORIA_2019_paquete_v1.zip` pasa la comprobación de integridad de todos sus miembros. Contiene código, configuración y pruebas; no contiene los modelos ni resultados de la corrida.
- `historia.py`, `historia_features.py`, `historia_metrics.py` y `requirements.txt` coinciden byte a byte con las fuentes recuperadas de la VM y publicadas en Segunda_competencia dentro de la auditoría v2.
- V6 tiene cierre de 165 ajustes y evaluación de octubre publicada. Sus archivos privados están identificados por hashes. No se encontró un respaldo privado local en las ubicaciones revisadas: workspace, otras carpetas Codex, Escritorio y Descargas. Esto no demuestra que no exista en otro lugar.
- No se eliminó nada de v1 o v6 durante esta revisión local. No hay conexión local autenticada a Google Cloud y el navegador disponible permite lectura, no escritura en la terminal.

## Procedimiento preparado

`herramientas/respaldar_limpiar_v1_v6.py` se ejecuta en Cloud Shell. Requiere VM apagada al comenzar; no interrumpe una corrida activa. Establece límite de una hora de VM para este trabajo de respaldo, apagado de respaldo a los 55 minutos y apagado al terminar o fallar. No entrena.

1. Verifica los agregados, los modelos y predicciones de v6, el código original de entrenamiento y el dataset contra hashes publicados.
2. Recupera v1: fuentes, resultados, piloto, revisiones y log si están presentes. Recupera v6 y dataset. Omite entornos/cachés, que conserva en VM; documenta lo omitido.
3. Solo excluye del paquete las matrices de entrenamiento v6 identificadas por su hash y las once matrices de octubre, regenerables con el código ejecutado, cuyos modelos y predicciones sí se respaldan. No excluye otros archivos por extensión o tamaño. Rechaza enlaces no auditados.
4. Crea archivo privado y manifiesto por miembro. Transfiere en partes de 32 MiB, con hasta tres intentos por parte, para evitar repetir todo el archivo ante una interrupción de red durante esa ejecución.
5. En Cloud Shell verifica cada parte, el archivo completo y todos sus miembros. Si faltan archivos, cambia un hash o no hay espacio, no limpia.
6. Vuelve a verificar que los archivos de origen no cambiaron. Solo entonces elimina las matrices v6 preidentificadas y registra cada hash/tamaño antes y después. No elimina modelos, predicciones, fuentes, metadatos, dataset ni ningún archivo v1.
7. Guarda informe, inventario, comprobante y respaldo en `~/respaldo_v1_v6_FECHA_HORA/`. Apaga la VM y muestra su estado final. Si falla una transferencia o un límite corta el proceso, se conservan los originales; no presentar el trabajo como terminado.

La copia en Cloud Shell queda fuera de la VM, pero **todavía debe descargarse a la computadora** para certificar también ese respaldo local. El script no publica archivos privados en Git. Un ZIP de código o un inventario de hashes no sustituye esa copia. No se afirma reproducción independiente del experimento por completar la recuperación.

## Alcance de limpieza

Hasta 11 matrices de entrenamiento y 11 de octubre en la corrida v6 completada. No limpia otras corridas, entornos, C1/C3 ni v1. Los nuevos archivos privados de respaldo en VM se conservan; el espacio neto libre puede crecer menos que el tamaño bruto de matrices eliminadas.

Siete pruebas locales aprobadas: paquete válido, contenido alterado, miembro faltante, extra, duplicado, bloqueo por hash incorrecto y lista limitada de candidatos. No equivalen a una prueba integral en Google Cloud. El resultado real permanece pendiente hasta recibir el informe del controlador.

## Incidente y recuperación directa local

El controlador ejecutado el 14/11 terminó de preparar el paquete, pero se detuvo por espacio insuficiente en Cloud Shell antes de descargarlo o limpiar. La VM quedó TERMINATED. La comprobación anterior exigía dos copias simultáneas; se corrigió con ensamblado incremental y reanudación de prefijos verificados (nueve pruebas pasan).

Por pedido posterior de Clara, el destino definitivo es la computadora local. `habilitar_rescate_local.py` habilita únicamente una clave pública dedicada y temporal (caduca en una hora, sin forwarding ni PTY), informa la clave del host para verificarla y mantiene apagado máximo independiente. No contiene claves privadas. Esta habilitación requiere una ejecución desde la sesión Cloud Shell autenticada. Luego se puede transferir directamente con SSH, verificar el archivo y todos los miembros localmente y, solo entonces, enviar el comprobante al limpiador. No usar ese comprobante antes de la verificación real.

El incidente no implica pérdida de originales ni autoriza borrar todo: se conserva el alcance de matrices v6 identificadas. V1 se recupera y conserva. La habilitación deja la VM encendida para la transferencia; debe retirarse la clave dedicada y detener la VM al concluir. El paquete ya creado se reutiliza, no se vuelve a construir.

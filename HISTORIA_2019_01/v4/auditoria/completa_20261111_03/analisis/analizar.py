from pathlib import Path
import json,statistics as st,math,hashlib
p=Path(__file__).parent;d=json.loads((p/'evidencia_original.json').read_text());arms=['B0','F1','F3','F4a','F4b'];out=p;out.mkdir(exist_ok=True)
for name,value in d.items():
 f=out/'metricas'/f'{name}.json';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
b=d['B0/result'];rows=[];ens=[];hp=[];seeds=[];checks=[]
for a in arms:
 r=d[a+'/result'];s=r['seeds'];t=d[a+'/trials'];best=d[a+'/best'];au=[x['auc'] for x in s];ga=[x['gain']['smoothed_gain_max'] for x in s]
 assert len(t)==10 and len(s)==5 and [x['seed'] for x in s]==[101,211,307,401,503]
 assert best['auc']==max(x['auc'] for x in t) and abs(s[0]['auc']-best['auc'])<1e-12
 assert all(x['rounds']<1500 for x in t)
 da=[x['auc']-y['auc'] for x,y in zip(s,b['seeds'])];dg=[x['gain']['smoothed_gain_max']-y['gain']['smoothed_gain_max'] for x,y in zip(s,b['seeds'])]
 if a!='B0':
  c=next(x for x in d['comparisons'] if x['arm']==a and x['control']=='B0');assert math.isclose(st.mean(da),c['delta_auc_mean'],abs_tol=1e-12);assert math.isclose(st.mean(dg),c['delta_gain_mean'],abs_tol=1e-6)
 rows.append({'arm':a,'columns':r['columns'],'auc_mean':st.mean(au),'auc_sd':st.stdev(au),'gain_mean':st.mean(ga),'gain_sd':st.stdev(ga),'delta_auc':st.mean(da),'delta_gain':st.mean(dg),'gain_pct':100*st.mean(dg)/st.mean(x['gain']['smoothed_gain_max'] for x in b['seeds']),'auc_wins':sum(x>0 for x in da),'gain_wins':sum(x>0 for x in dg),'fit_minutes':(sum(x['seconds'] for x in t)+sum(x['seconds'] for x in s))/60})
 e=r['ensemble_gain'];ens.append(f"| {a} | {r['ensemble_auc']:.6f} | {e['smoothed_gain_max']/1e6:.3f} | {e['point_gain_at_cut']/1e6:.3f} | {e['cut_contacts']} | {100*e['contact_proportion']:.3f}% |")
 h=best['params'];hp.append(f"| {a} | {h['num_leaves']} | {h['learning_rate']:.5f} | {h['min_data_in_leaf']} | {h['feature_fraction']:.4f} | {h['bagging_fraction']:.4f} | {best['rounds']} | {best['trial']+1} |")
 for x,y in zip(s,b['seeds']):seeds.append(f"| {a} | {x['seed']} | {x['auc']:.6f} | {x['gain']['smoothed_gain_max']/1e6:.3f} | {x['auc']-y['auc']:+.6f} | {(x['gain']['smoothed_gain_max']-y['gain']['smoothed_gain_max'])/1e6:+.3f} |")
(out/'resumen_calculado.json').write_text(json.dumps(rows,indent=2)+'\n')
text='''# Análisis del experimento HISTORIA 2019 v4

Corrida `completa_20261111_03`. Análisis: 13/11/2026. Etapa corta exploratoria completa; el proyecto entero tiene etapas pendientes.

## Conclusión

B0 se mantiene como referencia por la regla predefinida de AUC. Ninguna alternativa tuvo diferencia media de AUC positiva y al menos cuatro victorias en cinco semillas. Eso no equivale a demostrar que todas las familias son inútiles: F3 tiene una señal económica favorable y F1 mejora al promediar las predicciones de las semillas. Ambos hallazgos son exploratorios. F4a y especialmente F4b fueron desfavorables bajo este diseño.

## Qué se ejecutó

- 507.328 filas cliente-mes de entrenamiento: marzo, abril, mayo y junio de 2019, sin muestreo. No son 507.328 clientes únicos.
- 131.887 clientes en agosto para validación. Enero y febrero aportan historia a marzo; los demás meses de entrenamiento usan sus propios meses previos. Agosto usa junio, julio y agosto.
- LightGBM entrenado con BAJA+1 y BAJA+2 como positivos. AUC de agosto: BAJA+2 positiva; el resto negativo. Esta diferencia está declarada y fue idéntica en los cinco brazos.
- 10 pruebas Optuna por brazo, mismo espacio y presupuesto, AUC como objetivo y early stopping de 100 rondas. Después se congelaron parámetros e iteraciones y se ajustaron cinco semillas: 101, 211, 307, 401, 503.
- Total: 50 búsquedas + 25 reajustes = 75 ajustes. 9.133 segundos, aproximadamente 2 h 32 min. Finalización correcta, sin corte por recursos; máximo de memoria del proceso observado: 16,84 GiB. No es medición de costo monetario.
- Octubre no se evaluó. La VM quedó apagada después de recuperar los agregados.

## Variables: qué significa cada alternativa

| Brazo | Contenido | Columnas finales |
|---|---|---:|
| B0 | Variables actuales + rezagos de uno y dos meses + cambios absolutos frente a esos meses | 652 |
| F1 | B0 + promedio, mínimo, máximo y rango de tres observaciones | 1.156 |
| F3 | B0 + cambios relativos frente al promedio, al mes anterior y a dos meses atrás | 1.030 |
| F4a | B0 + posición relativa de cada cliente dentro del mismo mes | 778 |
| F4b | F4a + rezagos, cambios y resúmenes de esas posiciones relativas | 1.786 |

Se construyó historia sobre 129 variables fuente revisadas. El conjunto inicial de B0 tenía 152 variables actuales + 516 históricas = 668; quedaron 652 tras retirar seis completamente vacías en entrenamiento y diez duplicadas exactas. No se aplicaron canaritos ni selección por importancia en esta etapa.

W3 significa **mes actual y dos meses anteriores**, no tres meses anteriores. Si los valores cronológicos son 100, 80 y 60: lag1=80; lag2=100; delta1=-20; delta2=-40; promedio=80; mínimo=60; máximo=100; rango=40. Los cambios relativos son -25% frente al mes previo/promedio y -40% frente al primer mes. La fórmula es `(actual-referencia)/abs(referencia)`.

Los ranks se calculan como rango promedio de empates dividido por cantidad de valores no nulos, dentro de cada mes. Representan posición en la población, no dinero ni probabilidad. F4b compara la posición del cliente en poblaciones de meses distintos.

Todas las ampliaciones parten de B0; F4b además contiene F4a y se compara contra ambos. Esta rama prueba nuevas representaciones de la misma historia corta, **no el beneficio de disponer de más meses**. No tiene un brazo RAW sin historia: por tanto no estima el salto de RAW a lags/deltas.

## Resultados individuales: media de cinco semillas

Ganancia en millones de unidades monetarias según la regla del concurso. Es el máximo de la curva acumulada suavizada en agosto, no ganancia futura realizada.

| Brazo | AUC medio | DE AUC | Ganancia media M | DE ganancia M | Δ ganancia M vs B0 | Δ ganancia % | Victorias AUC | Victorias ganancia |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''
for r in rows:text+=f"| {r['arm']} | {r['auc_mean']:.6f} | {r['auc_sd']:.6f} | {r['gain_mean']/1e6:.3f} | {r['gain_sd']/1e6:.3f} | {r['delta_gain']/1e6:+.3f} | {r['gain_pct']:+.2f}% | {str(r['auc_wins'])+'/5' if r['arm']!='B0' else '—'} | {str(r['gain_wins'])+'/5' if r['arm']!='B0' else '—'} |\n"
text+='''
DE = desviación estándar entre semillas. Mide sensibilidad al azar del entrenamiento, no estabilidad entre meses ni incertidumbre sobre nuevos clientes. Las semillas no constituyen cinco datasets independientes.

F1 queda muy cerca del baseline: ΔAUC=-0,000221 y Δganancia=-0,28%; no hay mejora consistente por semilla. F3 pierde AUC (-0,001060) pero gana 2,918 M (+1,42%) en promedio y gana económicamente en cuatro semillas. Es compatible con mejorar la parte del ranking que interesa contactar aunque empeore su orden global; no identifica por sí solo la causa.

F4a pierde 6,228 M (-3,03%) y no gana económicamente en ninguna semilla. F4b pierde AUC y ganancia en las cinco semillas frente a B0; también pierde AUC en las cinco frente a F4a. Frente a F4a, su pérdida económica media es 3,073 M, aunque gana en dos semillas. El resultado de F4b no justifica continuar aumentando ese paquete sin una hipótesis nueva.

## Al combinar las cinco semillas

Se promedian las predicciones de los cinco modelos y se evalúa un solo ranking. Esto es distinto de promediar sus cinco ganancias.

| Brazo | AUC combinado | Ganancia suavizada M | Ganancia puntual al corte M | Contactos | Población contactada |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(ens)+'''

F1 combinado mejora AUC en 0,000374 y ganancia suavizada en 3,198 M (+1,55%) respecto de B0. Sin embargo, su ganancia puntual en el corte elegido es 0,468 M menor que la de B0 en su propio corte. No se debe confundir ganancia suavizada con el pago exacto de una lista concreta.

F3 combinado mejora la ganancia suavizada en 2,733 M (+1,32%) y la puntual en 2,090 M, pero pierde AUC en 0,000578. F4a y F4b combinados empeoran ambas métricas frente a B0. No hay una mejora demostrada del 5%.

Las alternativas eligen distintas cantidades de contactos; esta comparación no responde a una campaña con idéntico número de contactos para todos. La curva suavizada usa una ventana completa de 2.001 posiciones, busca su máximo en agosto y evalúa la ganancia puntual en el centro de ese tramo. Ambos cálculos aprovechan las etiquetas de agosto: son diagnósticos de validación, no test independiente. BAJA+2 aporta +1.072.500 y cualquier otra clase -27.500 por contacto. No se usa un umbral probabilístico porque el score no es una probabilidad calibrada de BAJA+2.

## Hiperparámetros y costo de cada alternativa

Se optimizó cada representación por separado, siguiendo la indicación de Ale. Los parámetros coincidentes en algunos brazos fueron seleccionados por búsquedas independientes con la misma semilla del optimizador; no fueron heredados del baseline. Misma cantidad de pruebas no garantiza haber encontrado el óptimo de cada representación.

| Brazo | Hojas | Learning rate | Mínimo por hoja | Fracción features | Fracción filas | Árboles | Prueba ganadora (1–10) |
|---|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(hp)+'\n\n'
for r in rows:text+=f"- {r['arm']}: {r['fit_minutes']:.1f} minutos sumados de entrenamiento de sus 15 ajustes.\n"
text+='''
F4b consumió aproximadamente 3,63 veces el tiempo de B0 con 2,74 veces sus variables y peores resultados. Ninguna mejor iteración de las 50 pruebas alcanzó el tope de 1.500; esto descarta ese tope como explicación directa, pero no prueba que diez pruebas de hiperparámetros sean suficientes.

La semilla 101 se usó para elegir hiperparámetros y volvió a incluirse en las cinco semillas. Su reajuste reproduce el AUC de la prueba ganadora; no es confirmación independiente. Como sensibilidad, al excluir 101, F3 conserva Δganancia media positiva de 1,655 M y gana en tres de cuatro semillas, pero conserva ΔAUC negativa (-0,000947). No cambia el veredicto de la regla original. Esta sensibilidad no reemplaza la evaluación predefinida.

## Calidad de datos y verificaciones

Se preservaron nulos; no se imputaron como cero. Los nueve pares variable-mes adoptados como rotos se enmascararon antes de construir historia, con la misma regla en todos los brazos. Su aplicación consistente no sustituye la validación de negocio de esas máscaras. Los rezagos se unen por cliente y mes calendario exacto, sin saltar meses ausentes.

La receta de F1 y F3 exige tres observaciones no nulas; F3 además exige denominador distinto de cero. Para los cambios relativos frente al mes previo también se exige la ventana completa, aunque la fórmula aislada usaría solo dos observaciones. Esta decisión restrictiva debe declararse.

| Variables adicionales | Mediana cobertura marzo | Abril | Mayo | Junio |
|---|---:|---:|---:|---:|
| F1 | 97,6% | 98,0% | 97,9% | 97,2% |
| F3 | 29,2% | 25,1% | 18,5% | 18,4% |
| F4a | 100% | 100% | 100% | 100% |
| F4b respecto de B0 | 97,6% | 98,0% | 97,9% | 97,2% |

Son medianas de cobertura por columna, no porcentaje de clientes con todas las variables completas. En junio hay 36 columnas adicionales de F1 totalmente vacías y 27 de F3. Los meses rotos se propagan a las ventanas siguientes. La caída de cobertura de F3 es compatible con sus restricciones y denominadores cero; no se cuantificó aquí cuánto corresponde a cada causa. No corresponde cambiar retrospectivamente la fórmula y presentar el nuevo resultado como la misma prueba.

Se verificaron el hash de la copia local de métricas frente a Cloud Shell, los 10 trials y cinco semillas por brazo, la elección del máximo AUC de Optuna, la reproducción de la semilla 101 y las diferencias pareadas recalculadas. El registro confirma la reutilización de las matrices previas con hash verificado. El runner, motor de variables y supervisores locales coinciden con sus hashes de ejecución. El auxiliar de calibración difiere de la copia de trabajo; no fue ejecutado por esta corrida completa. No se repitió el entrenamiento ni se inspeccionaron predicciones individuales en esta revisión.

## Alcance y decisión

Mantener B0 según el criterio acordado. Conservar F3 como hipótesis económica y F1 como hipótesis de ensemble, sin llamarlos ganadores confirmados. No seleccionar retrospectivamente la métrica más favorable para declarar éxito.

Antes de gastar más: acordar con Ale si la siguiente decisión se basa en la ganancia del ensemble o en la regla exploratoria de AUC por semilla. Si se hace una confirmación, fijar previamente candidatos, métrica y presupuesto y usar semillas distintas de las usadas para optimizar. Más semillas evalúan azar algorítmico; no resuelven el uso repetido de agosto.

Octubre sigue siendo el test final según la consigna. Antes de abrirlo deben congelarse modelos, recetas, combinación de semillas y política de contacto. La política ya escrita propone fijar la proporción de contactos elegida en agosto para cada brazo y aplicarla en octubre sin buscar un nuevo máximo. Una vez visto octubre, no se debe usar para retocar familias o cortes y conservar la etiqueta de test independiente.

Pendientes del proyecto, no ejecutados en estos 75 ajustes: historia de cuatro/seis observaciones con baseline entrenado en el mismo calendario; tendencias de ventanas largas; canaritos; combinaciones de familias; confirmación de 20 semillas; evaluación de octubre. La pendiente lineal en tres puntos equiespaciados coincide numéricamente con delta2/2 en ventanas completas, por eso se dejó fuera; su máscara de nulos puede diferir de la de delta2. El experimento completo de esta etapa no equivale al programa entero propuesto por Ale.

Para mirar al futuro, la pregunta pendiente es si acumular más meses permite mejorar con historia más larga sin confundir esa mejora con cambiar las filas de entrenamiento. Esa rama necesita su propio control con el mismo calendario. Los resultados de 2019 no permiten afirmar rendimiento en pandemia ni en 2020.

No se mezclan numéricamente estos resultados con v1/v2/v3: deben verificarse antes su baseline, clase positiva de AUC, suavizado, semillas y forma de elegir el corte. Un nombre de familia o un AUC parecido no garantiza comparabilidad.

## Preguntas concretas para Ale

1. F3 gana 1,42% de ganancia media pero pierde AUC: ¿confirmamos su ganancia como hipótesis declarada, manteniendo AUC para Optuna?
2. F1 mejora al combinar cinco modelos pero no en la media individual: ¿la unidad final de comparación será el ensemble?
3. ¿Mantenemos la media móvil de ganancia de 2.001 contactos y reportamos además ganancia puntual y tamaño de campaña?
4. ¿Aceptamos la regla estricta de tres observaciones para todos los ratios, o evaluamos otra receta como un experimento distinto?
5. Para historia larga, ¿confirmamos junio como entrenamiento común y baseline reoptimizado en esas mismas filas?

## Detalle por semilla

| Brazo | Semilla | AUC | Ganancia suavizada M | ΔAUC vs B0 | Δganancia M vs B0 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(seeds)+'''

## Procedencia y conservación

Fuente: `completa_20261111_03_agregados.tar.gz`, recuperado del propietario en Cloud Shell. SHA256 del archivo: `eba6495a19c17c235f75108a71220e829a28a9be753008fb79087069f8f8cc7b`.

Se copió un subconjunto exacto de 22 objetos JSON (resultados, búsquedas, parámetros, comparaciones e identidades), verificado con SHA256 `7ff9d67b863d504d425bdaf9fe696c2d5c5f1684d620b758772fae4dbd137a8e`. Esos objetos y el análisis se guardan localmente; el archivo agregado completo continúa en Cloud Shell. El manifiesto de cobertura se consultó allí; la tabla de cobertura es una transcripción de su resumen redondeado. No se copian datos de clientes ni modelos a Git. Este guardado no constituye un push a GitHub.
'''
(out/'INFORME.md').write_text(text)
print('Verificados 50 trials, 25 semillas y 4 comparaciones pareadas; informe generado')

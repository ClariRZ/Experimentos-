from pathlib import Path
import json, statistics as st, hashlib, csv, shutil, argparse
from decimal import Decimal,ROUND_HALF_UP
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
ap=argparse.ArgumentParser();ap.add_argument('--work',default='work/informe_prompts_2019');ap.add_argument('--output',default='outputs/informe_prompts_2019');args=ap.parse_args();W=Path(args.work);OUT=Path(args.output);OUT.mkdir(exist_ok=True,parents=True)
D=json.loads((W/'evidencia.json').read_text());models=D['models'];M={(m['version'],m['arm']):m for m in models};doc=Document();md=[]
sec=doc.sections[0];sec.page_width=Inches(8.27);sec.page_height=Inches(11.69);sec.top_margin=Inches(.68);sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.7)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
 s=doc.styles[name];s.font.name='Liberation Sans';s.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(10.5);doc.styles['Normal'].paragraph_format.space_after=Pt(6);doc.styles['Normal'].paragraph_format.line_spacing=1.08
for node in doc.styles.element.xpath('.//w:pBdr'):node.getparent().remove(node)
for name,size in [('Title',24),('Heading 1',18),('Heading 2',13)]:doc.styles[name].font.size=Pt(size)
doc.core_properties.title='Informe de los experimentos de historia 2019 v4 v5 y v6';doc.core_properties.subject='Prompts ejecutados resultados y bases para el siguiente experimento';doc.core_properties.author='Clara Rodríguez'
p=sec.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;p.add_run('Historia 2019  |  ')
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
for r in p.runs:r.font.size=Pt(8)
def para(s,bold=False):
 p=doc.add_paragraph();p.add_run(s).bold=bold;md.append(s+'\n');return p
def heading(s,level=1):doc.add_heading(s,level);md.append('#'*(level+1)+' '+s+'\n')
def page(title):
 if doc.paragraphs or doc.tables:doc.add_page_break()
 heading(title)
def fmt(n,d=4,sign=False):
 if n is None:return 'Pendiente'
 v=Decimal(str(n)).quantize(Decimal(1).scaleb(-d),rounding=ROUND_HALF_UP);s=f'{v:,.{d}f}'.replace(',','@').replace('.',',').replace('@','.')
 return ('+' if sign and n>0 else '')+s
def mil(n,sign=False):return fmt(n/1e6,4,sign)
def table(headers,rows,widths=None,size=9.5):
 t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 if widths is None:widths=[6.87/len(headers)]*len(headers)
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 for c,x in zip(t.rows[0].cells,headers):c.text=str(x)
 for row in rows:
  cells=t.add_row().cells
  for c,x in zip(cells,row):c.text=str(x)
 for i,row in enumerate(t.rows):
  for j,c in enumerate(row.cells):
   c.width=Inches(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   pr=c._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'263D51' if i==0 else ('F0F3F5' if i%2==0 else 'FFFFFF'));pr.append(sh)
   borders=OxmlElement('w:tcBorders')
   for e in ['top','left','bottom','right']:
    x=OxmlElement('w:'+e);x.set(qn('w:val'),'single');x.set(qn('w:sz'),'4');x.set(qn('w:color'),'D9D9D9');borders.append(x)
   pr.append(borders);margin=OxmlElement('w:tcMar')
   for e,val in [('top',55),('bottom',55),('left',80),('right',80)]:
    x=OxmlElement('w:'+e);x.set(qn('w:w'),str(val));x.set(qn('w:type'),'dxa');margin.append(x)
   pr.append(margin)
   for p in c.paragraphs:
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0
    for r in p.runs:r.font.size=Pt(size);r.font.name='Liberation Sans';r.font.bold=i==0;r.font.color.rgb=RGBColor(255,255,255) if i==0 else RGBColor(0,0,0)
  trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
 t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
 md.append('| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(str(x).replace('\n',' / ').replace('|','¦') for x in row)+' |' for row in rows)+'\n')
 doc.add_paragraph().paragraph_format.space_after=Pt(1)

doc.add_paragraph('Informe de los experimentos de historia 2019 v4 v5 y v6','Title');md.append('# Informe de los experimentos de historia 2019 v4 v5 y v6\n')
para('Secuencia de prompts, resultados verificables y bases para el próximo protocolo',True)
para('Clara Rodríguez · Corte documental del 13 de noviembre de 2026')
para('El resultado más defendible es una lista de hipótesis con evidencia desigual, no un ganador universal. V4 no promovió ninguna familia bajo su regla original de AUC. V5 priorizó mínimo, rango y promedio por ganancia de agosto; octubre sigue pendiente. V6 priorizó T4, R3 y R4 en agosto y los tres mejoraron también en octubre, con cinco de cinco semillas favorables.')
para('Este informe cubre los tres experimentos recientes: v4, archivado como experimento_2026-11-13; v5, descomposición de historia corta; y v6, profundidad histórica. V1–v3 y C3 son antecedentes y no se suman a sus cifras. Se separan propuesta, ejecución y evaluación posterior. No se ejecutó ningún ajuste nuevo para elaborar el informe.')
table(['Versión','Pregunta ejecutada','Ajustes','Estado'],[['v4','Familias cortas frente al mismo B0','75','Agosto y octubre'],['v5','Componentes separados y retiro de deltas','105','Agosto completo'],['v6','Ventanas y representaciones con junio común','165','Agosto y octubre']],[.7,3.65,.65,1.87])
para('Son 23 brazos, 230 ajustes Optuna y 115 reentrenamientos por semilla: 345 ajustes registrados. Las evaluaciones de octubre reutilizaron modelos congelados. Duración registrada del desarrollo: v4 2 h 32 min, v5 2 h 26 min, v6 1 h 24 min; no son horas totales de VM ni facturación. No equivalen a 345 modelos independientes ni a 345 pruebas temporales.')
heading('Cómo leer este informe',2)
para('Primero se reconstruyen los prompts y las reglas. Luego se sintetizan los resultados y las hipótesis. El anexo contiene una ficha y una tabla por cada uno de los 23 brazos, incluidos los controles y los resultados negativos. Los archivos de apoyo conservan parámetros completos, nombres de columnas disponibles, métricas por semilla y hashes de las fuentes.')
para('Las cifras monetarias se expresan en millones de pesos de la regla del concurso, no en ingresos efectivamente cobrados. Ninguna suma de mejoras entre modelos representa una ganancia acumulable. “Superador” siempre debe acompañarse de control, mes, métrica y criterio.')

page('1 La secuencia real de prompts')
heading('V4 de una auditoría amplia a cinco brazos',2)
para('El archivo 01_prompt_original.txt era un protocolo corregido de auditoría y pruebas sintéticas, con cero entrenamientos en esa etapa. Describía además futuras combinaciones, canaritos y una rama W3/W4/W6; mencionaba presupuestos posteriores de 50 trials y 20 semillas. No es evidencia de haber corrido ese alcance. Su filtro de cobertura del 90 % quedó reemplazado por el plan adaptado.')
para('El plan 02_plan_adaptado.md eliminó el filtro automático del 90 %, mantuvo faltantes y limitó la primera comparación a B0, F1, F3, F4a y F4b. Proponía dos mediciones y 75 ajustes, con un techo inicial de dos horas. El contrato definitivo cambió ese presupuesto: cero pilotos dentro de esa corrida, 75 ajustes y techo de 16 horas después de la calibración. El tiempo registrado del trabajador fue 2 h 32 min; no es el tiempo de toda la preparación.')
para('El contrato 03_contrato_ejecutado.json es idéntico al contrato original de la carpeta reproducible y describe la corrida completa_20261111_03. Octubre tuvo un protocolo y autorización posteriores. La fecha de la carpeta 13/11 corresponde a organización y cierre; no debe confundirse con la fecha de inicio de entrenamiento.')
heading('V5 separar lo que estaba combinado',2)
para('El prompt maestro v5 mantuvo el objetivo de incorporar historia en un proceso reutilizable. Cambió la prioridad económica: AUC siguió eligiendo hiperparámetros, pero la ganancia del ensemble y la estabilidad individual pasaron a decidir qué confirmar. Separó F1 en promedio, mínimo, máximo y rango; agregó el retiro de deltas. Su segunda etapa de historia larga y las pruebas de canaritos, combinaciones y faltantes quedaron condicionadas a contratos propios.')
para('La corrida entrenamiento_20261113_01 ejecutó solamente siete brazos, 105 ajustes y cinco semillas distintas de la usada en Optuna. No ejecutó octubre ni la rama larga del prompt. El estado histórico “sin entrenamientos” de procedencia.json describe cuándo se guardó el prompt, no el cierre actual. El config congelado también conserva un texto de estado antiguo; los campos de autorización, los resultados y el registro de corrida deben leerse juntos.')
heading('V6 hacer explícita la rama de profundidad',2)
para('El prompt v6 separó la pregunta pendiente y fijó once brazos, 18 contrastes y 165 ajustes. Todos usan junio, incluido B0_J, para disponer de historia desde enero sin cambiar las filas entre controles y candidatos. No dependía de que alguna familia ganara en v5. La corrida completa es v6_20261113_02; el cierre octubre_v6_01 se autorizó y ejecutó después, sin reentrenamiento. El sufijo de corrida no es el número de versión del experimento. El intento v6_20261113_01 se detuvo en preparación por un timeout de despacho SSH, con cero ajustes completados; el incidente y la corrección quedaron registrados antes de la corrida _02.')
para('No se reescriben los prompts históricos para hacerlos coincidir con los resultados. El próximo protocolo deberá conservar esta cadena y establecer una única especificación ejecutable sin estados contradictorios. Fuentes P4, P5 y P6 en el índice final.')

page('2 Reglas de datos y significado de las variables')
para('Se usó el mismo archivo analistasr_competencia_2026.csv.gz, identificado por SHA256 459c6229eeae81677add6dbcd1b7ecb1d3121f2d5b7367593bc5a5c58834c872. Las etiquetas ya vienen en ese archivo. No se reconstruyeron desde el crudo de Ezequiel. V4/v5 entrenan 507.328 filas de marzo–junio; v6 entrena 128.474 filas de junio. Agosto tiene 131.887 clientes y octubre 135.754. No se hizo sampling ni ponderación adicional de BAJA+2.')
para('Se conservaron 152 variables originales como punto de partida y 129 fuentes candidatas para construir historia, revisadas semánticamente. No son 129 variables finales: las derivaciones y la depuración cambian el número de columnas. Identificador, mes y clase quedan fuera de los predictores. Las listas ordenadas de columnas de los 23 brazos se adjuntan en evidencia.json; las de v4 se recuperaron en la auditoría complementaria y se contrastan con el protocolo de octubre.')
table(['Mes','Variables saneadas como nulas'],[['Abril 2019','ctarjeta_visa_debitos_automaticos; mttarjeta_visa_debitos_automaticos'],['Mayo 2019','mrentabilidad; mrentabilidad_annual; mcomisiones; mactivos_margen; mpasivos_margen; mcomisiones_otras; ccomisiones_otras']],[1.05,5.82])
para('Son nueve pares variable–mes, no una garantía de ausencia de otras anomalías. Se aplican antes de generar historia y de la misma forma a todos los brazos. Se preservan nulos y negativos válidos; los no finitos pasan a nulos. No se convierte automáticamente una ausencia de producto en cero. Los rezagos unen cliente y mes calendario exactos; una fila anterior disponible no sustituye un mes faltante.')
table(['Derivado','Definición y política'],[['Lag k','Valor del mismo cliente k meses antes. Si falta la fila o el valor, NA.'],['Delta k','Actual menos lag k. Requiere ambos extremos; no todos los meses intermedios.'],['Media mínimo máximo rango','Sobre W observaciones consecutivas, incluida la actual. Rango = máximo − mínimo. Exigen ventana completa no nula.'],['Cambio relativo','(actual − referencia) / abs(referencia). Referencias: media W, lag1 y lag W−1. Ventana completa y referencia distinta de cero; en otro caso NA.'],['Tendencia','Pendiente OLS contra tiempo 0 a W−1; cambio por mes. W4 y W6. Con tres puntos completos equivale a delta2/2.'],['Ranking mensual','Rango promedio entre clientes del mismo mes dividido por cantidad no nula. Incluye ceros y negativos; nulos permanecen nulos.']],[1.55,5.32])
para('Depuración solo con entrenamiento: vacías, constantes incluyendo el patrón de nulos y duplicadas exactas en la representación del modelo. Se preserva un valor finito más nulos si ese patrón varía. V6 congela pares fuente–fórmula comunes dentro de S, T y R para comparar ventanas; no elimina clientes sin historia completa. Más ventana implica también menos cobertura, un componente real del tratamiento.')

page('3 Qué optimizamos y qué medimos')
para('Todos los brazos son LightGBM binarios con boosting por árboles. Entrenamiento positivo = BAJA+1 o BAJA+2; validación AUC positiva = BAJA+2. El score sirve para ordenar clientes y no es una probabilidad calibrada de BAJA+2. No se usaron canaritos, pesos extra, nuevos algoritmos ni bagging externo de filas en estas tres corridas.')
table(['Hiperparámetro','Espacio común'],[['num_leaves','16–128 entero logarítmico'],['learning_rate','0,01–0,1 logarítmico'],['min_data_in_leaf','100–2.000 entero logarítmico'],['feature_fraction','0,3–1,0'],['bagging_fraction','0,5–1,0']],[2.5,4.37])
para('Cada brazo recibió Optuna TPE con 10 trials, 5 iniciales, sampler seed 20261111 y modelo seed 101. Máximo 1.500 árboles, early stopping de 100 por AUC de agosto; se elige el mayor AUC y, ante empate, el primer trial. Fijos explícitos: bagging_freq=1, cuatro hilos, deterministic=true, force_col_wise=true, objective=binary, metric=auc y feature_pre_filter=false. El runner fija además las semillas internas de LightGBM. Los parámetros no explicitados dependen de la versión registrada y deben exportarse en el próximo protocolo.')
para('V4 evaluó 101, 211, 307, 401 y 503: la semilla 101 ya había participado de Optuna. V5/v6 corrigen esa dependencia usando 211, 307, 401, 503 y 601. Tras Optuna se congelan hiperparámetros y árboles, sin early stopping nuevo por semilla. El ensemble promedia scores alineados por cliente. Su ganancia no es el promedio de las ganancias individuales. Cada brazo se optimiza por separado, aunque dos búsquedas pueden elegir los mismos valores: R3 y R4 comparten los cinco hiperparámetros, con 220 y 250 árboles respectivamente.')
heading('La regla económica exacta',2)
para('Ganancia = 1.072.500 × aciertos BAJA+2 − 27.500 × otros contactos. Equivalentemente, con k contactos y h aciertos: G = 1.100.000 × h − 27.500 × k. El premio ya es neto: no se descuenta otra vez el costo a un acierto.')
para('En agosto se ordena por score descendente y cliente ascendente. Se maximiza la media móvil centrada completa de 2.001 posiciones de la curva acumulada; empate, menor corte. Se guardan máximo suavizado, ganancia puntual en ese corte y proporción. El máximo suavizado es una medida de desarrollo optimizada en el mismo mes, no una estimación independiente de campaña futura.')
para('En octubre se aplica floor(proporción de agosto × 135.754), sin buscar otro corte. V4 aplica la proporción del ensemble a todas las semillas del brazo. V6 congela la proporción propia de cada semilla y del ensemble. Esta diferencia impide tratar sus victorias por semilla como una comparación idéntica entre versiones. Agosto y octubre además usan ganancias suavizadas y puntuales, respectivamente.')
para('El conteo 4/5 es una regla de asignación de cómputo, no una prueba de significación. Repetir semillas mide variabilidad del entrenamiento; no añade meses independientes. Reoptimizar por brazo con igual presupuesto mide una receta más su ajuste, no un efecto puro de variables con hiperparámetros fijos.')

page('4 Qué modelos fueron superadores y en qué sentido')
para('La tabla siguiente compara cada candidato con el control de su propia versión. Δ agosto corresponde al ensemble suavizado; Δ octubre al ensemble en el corte congelado. Las victorias son diferencias individuales positivas pareadas. M significa millones de pesos. Un control no compite contra sí mismo.')
rows=[]
for m in models:
 if m['arm']==m['base']:continue
 o=m['october'];rows.append([m['version']+' '+m['arm'],mil(m['summary']['ensemble_delta'],True),str(m['summary']['gain_wins'])+'/5',mil(o['summary']['ensemble_delta'],True) if o else 'Pendiente',str(o['summary']['wins'])+'/5' if o else '—','Sí' if m['eligible'] else 'No'])
table(['Brazo','Δ ago M','Gana ago','Δ oct M','Gana oct','Regla original'],rows,[.85,1.15,.8,1.15,.8,2.12],size=9)
para('V4: ningún candidato cumplió su regla de AUC. F1 dio el mayor ensemble de octubre, pero solo ganó en 2/5 semillas; F3 mejoró económicamente en ambos meses con 4/5; F4a pasó de perder en agosto a ganar en las cinco semillas de octubre. No se cambia retrospectivamente la selección original de B0.')
para('V5: MIN, RANGO y P cumplieron la regla económica de agosto. El paquete F1 no la cumplió aunque su ensemble subió. Ninguna variante mejoró el AUC medio individual contra B0; eso no impide una mejora económica. No se conocen ganancias de octubre de v5 en la evidencia versionada.')
para('V6: T4, R3 y R4 cumplieron la regla de agosto y ganaron en 5/5 semillas de octubre. R6 logró el mayor ensemble de octubre, pero había perdido en agosto y no era elegible. No conviene declararlo ganador robusto por elegir después el mes favorable. R3 superó a R4 en ganancia del ensemble de agosto; R4 lo superó en octubre. La evidencia no identifica una longitud óptima universal.')

page('5 Lectura de los resultados y límites de atribución')
heading('Qué aporta evidencia y qué sigue siendo una hipótesis',2)
para('Los cambios relativos muestran una señal útil: F3 en v4 y R3/R4 en v6 mejoraron la ganancia del ensemble en agosto y octubre. No son réplicas exactas: cambian calendario, fuentes efectivamente retenidas, hiperparámetros y semillas. T4 aporta una segunda familia con señal favorable en v6. MIN y RANGO son candidatos fuertes de agosto, pero aún no tienen cierre de octubre en v5.')
para('F1 de v5 combina cuatro componentes que por separado dieron ganancias positivas del ensemble, y sin embargo su mejora fue menor y poco estable. Posibles mecanismos son redundancia, dilución de variables útiles con feature_fraction, interacción de particiones, presupuesto de búsqueda escaso y azar del entrenamiento. Los datos no permiten elegir una explicación causal. Para demostrar interacción hacen falta el conjunto, sus componentes y controles reoptimizados bajo el mismo protocolo.')
para('La hipótesis de Ale de que los lags podrían bastar fue probada parcialmente por L en v5. Retirar deltas empeoró agosto. Eso respalda conservarlos en ese escenario; no demuestra que los deltas siempre sean necesarios ni contradice que un árbol más profundo pueda reconstruir diferencias. La búsqueda tiene solo diez trials por brazo.')
para('El ranking actual F4a fue fuerte en octubre pero débil en agosto. Agregar su historia F4b fue desfavorable frente a B0 y frente a F4a en octubre. Conviene distinguir ranking del nivel actual, ranking previo de montos e historia del ranking: no son la misma intervención. La rama de rankings sigue abierta como hipótesis específica, no como componente obligatorio del híbrido.')
heading('Por qué no se comparan millones entre versiones como una carrera',2)
para('B0 de v4 ganó 277,1450 M en octubre y B0_J de v6 261,8550 M. Ese contraste cambia cuatro meses de entrenamiento por uno, columnas, ajuste y política de cortes individuales. No mide cuánto “pierde la historia larga”. Cada mejora debe atribuirse contra su propio control. Tampoco se suman +15,125 M de R4 y +6,820 M de T4 para anticipar una combinación.')
para('Octubre ya había sido observado incluso antes de este ciclo de análisis. Congelar cortes protege contra optimizarlos con sus etiquetas, pero no devuelve independencia a un período conocido. Los nuevos híbridos tendrán evidencia exploratoria. Declarar esta condición es compatible con usar octubre como comparación económica solicitada por Ale.')
para('Los resultados de cinco semillas no justifican intervalos de precisión extrema ni afirmaciones de significancia por sí solos. No se calculó aquí un bootstrap nuevo porque requiere contribuciones o predicciones privadas, no solamente las métricas agregadas de Git. Tampoco se reprodujo todo el entrenamiento desde cero en otra máquina.')

page('6 Hipótesis de mejora derivadas de la tutoría')
para('La tutoría compartida por Clara orienta el diseño; el resumen siguiente es una paráfrasis, no una cita literal verificada contra una grabación. La consigna publicada fija 2019, LightGBM, entrenamiento marzo–junio sin sampling, BAJA+1 y BAJA+2 combinadas, AUC en agosto para optimizar y ganancia en octubre. Ale permite adaptar el baseline a la pregunta. La rama junio es una adaptación explícita.')
table(['Prioridad','Hipótesis y contraste','Razón y límite'],[['Primera','Completar octubre de los siete brazos de v5','Cerrar evidencia ya producida, sin elegir solo MIN o RANGO después de ver resultados. No implica reentrenar.'],['Primera','R4 + T4 frente a R4 y T4','La tendencia resume trayectoria y los relativos escala. Ambos funcionaron; complementariedad todavía no probada.'],['Primera','R4 + relativos simétricos frente a R4','Fórmula acotada de Ezequiel. Probar el paquete, sin atribuir su efecto solo a la fórmula si cambia cobertura.'],['Segunda','Relativos con máscara mínima frente a máscara W completa','Ale busca información útil; exigir meses no utilizados puede descartar señal. Mantener fórmula y fuentes para aislar faltantes.'],['Segunda','MIN o RANGO añadidos al control elegido','Señal consistente en agosto v5. Rehacer sobre junio si el control es de junio; no reutilizar marzo–junio.'],['Posterior','Ranking previo de montos y su historia','Responde al desplazamiento de escalas discutido por Ale. Limitar a montos y congelar universo mensual.'],['Posterior','Conjunto completo frente a filtrado con canaritos','Selección solo en entrenamiento, sin agosto en importancia, umbral ni early stopping del filtro. Reoptimizar ambos.'],['Posterior','Quiebres y caídas de actividad','Inspiración ACH_Q de Ezequiel; interpretable. Separar de tarjetas y pesos para saber qué aportó.'],['Posterior','Ventana de entrenamiento alternativa dentro de 2019','Evaluar estabilidad temporal y disponibilidad de historia con control idéntico. No usar 2020.']],[.7,2.6,3.57],size=9.5)
para('Ale advirtió que más variables cambia el efecto de feature_fraction y exige reoptimizar. Por eso no heredamos los parámetros ganadores de R4 para evaluar una unión más grande. También señaló que medias, extremos y tendencias facilitan a los árboles representar historia. El 3–5 % fue una magnitud interesante, no un umbral garantizado ni una exigencia para ocultar resultados negativos.')
para('Desvío estándar, varianza y promedios ponderados quedan en menor prioridad: en la tutoría se cuestionó su interpretabilidad y se prefirió estudiar rango y tendencias. Esto no demuestra que nunca funcionen. Tampoco se incorpora peso extra para BAJA+2, conforme a la decisión explícita de Clara.')

page('7 Qué tomar de la evaluación de Ezequiel')
para('La versión revisada es 770abaa9cad412647211c255360cb6dfe364e697. Sus aportes más útiles son comparación pareada por cliente y semilla, evaluación sobre varios meses con control temporal equivalente, bootstrap de clientes y comprobación de huellas de configuración y predicciones. No se copiaron sus ganancias ni se reentrenó su pipeline.')
para('Su bloque R calcula (actual − previo) / (abs(actual) + abs(previo)), para lag1 y lag2. Ambos valores cero producen cero; un faltante produce NA. El resultado queda entre −1 y 1. Nuestro cambio relativo divide por abs(referencia), conserva NA para denominador cero y exige W completa. Comparar ambas recetas tal cual cambia fórmula, referencias y cobertura; para atribuir solo a la fórmula hay que igualar los pares y la máscara primero.')
para('Su evaluación usa una banda de 3.000–6.000 contactos y promedia ganancia entre cortes, meses y semillas. El bootstrap remuestrea 2.000 veces clientes con sus contribuciones agregadas, conservando el vínculo de un cliente entre meses. Combina su error con la variación entre semillas. Es una herramienta más elaborada, no una prueba de que una mejora generalice a meses nuevos ni una corrección por búsqueda repetida.')
para('La regla de incorporación de cambios usa diferencia media positiva y al menos 3/5 semillas, sin exigir que el intervalo excluya cero. Incluye octubre: junio–octubre para ramas simples y septiembre–octubre para ramas que seleccionaron configuraciones. El README declara exploración. Ese uso no conserva octubre como un test independiente; no debe describirse como tal.')
para('Además, PAQ_P3 usa peso 3 para BAJA+2 y el control peso 1. La mejora del paquete no puede atribuirse solo a las variables. Sus tablas de +8,9986 M/mes contra AC y +12,5970 M/mes contra A-consigna corresponden a la referencia histórica PAQ_P3; el MAIN actual declara otros hiperparámetros. Antes de comparar hay que reconciliar configuración y tabla, y usar el mismo dataset, población y calendario que nosotros.')
heading('Cómo adaptar el bootstrap sin exagerar su alcance',2)
para('Para nuestro próximo experimento propongo un análisis pareado de diferencias de contribución económica por cliente a los cortes congelados, manteniendo juntos los meses del mismo cliente si se agrega una rama temporal. Debe registrarse antes la población de remuestreo, número de réplicas, semilla, normalización, intervalo y tratamiento de semillas. No copiar automáticamente la suma de errores ni suponer que el intervalo corresponde al ensemble si se construye a partir de ganancias individuales.')
para('Un bootstrap de contribuciones con selección fija describe incertidumbre condicional a los modelos y políticas ya elegidos. No vuelve a entrenar, no incluye toda la incertidumbre de Optuna y no reproduce por sí solo el cambio de ranking y del top-k al cambiar la población. Si se busca ese segundo estimando, se requiere un remuestreo que recalcule selección y un protocolo distinto. Esta distinción debe estar escrita antes de mostrar un “IC 95 %”.')

page('8 Base recomendada para el próximo prompt')
para('Recomiendo separar el cierre pendiente de v5 del nuevo entrenamiento. Después, formular un núcleo pequeño con controles suficientes para interpretar el híbrido. Esta propuesta amplía los tres brazos tentativos de la presentación anterior: agrega B0_J, R3 y T4 como referencias explícitas. Su presupuesto sería 90 ajustes, no 45. No se autoriza ni se ejecuta por incluirla en este informe.')
table(['Brazo propuesto','Contenido','Contraste principal'],[['B0_J','Baseline reconstruido en junio','Ancla común'],['R3','B0_J + relativos W3','R3 contra B0_J'],['R4','B0_J + relativos W4','R4 contra B0_J y R3'],['T4','B0_J + tendencia W4','T4 contra B0_J'],['H_T','Unión R4 y T4, sin duplicar B0_J','H_T contra R4 y T4'],['H_S','R4 + relativos simétricos lag1 y lag2','H_S contra R4']],[.8,3.3,2.77])
para('R3 se conserva porque ganó más que R4 en agosto; no se lo elimina solo porque R4 obtuvo mejor octubre. H_T probaría si juntar familias mejora el rendimiento, sin presuponer aditividad. H_S prueba un paquete adicional; una atribución aislada a fórmula o faltantes exige una comparación posterior diseñada para ese propósito.')
para('Condiciones propuestas: junio para todos; agosto para Optuna; octubre para comparación económica exploratoria. Mismo dataset, filas, fuentes, saneamiento y política de nulos. Diez trials propios más cinco semillas nuevas respecto de optimización por cada brazo. Primero auditoría sin entrenamiento; después 6 × (10 + 5) = 90 ajustes. Un aumento posterior de semillas debe incluir controles y candidatos pareados, con presupuesto separado.')
para('Las uniones deben partir de columnas congeladas y respetar prioridad del control al eliminar duplicados. Si la fórmula simétrica altera ceros y cobertura, documentar ambos cambios; no introducir simultáneamente ponderación, imputación, otro calendario o selección de fuentes por octubre. No mezclar medias ponderadas, canaritos y tarjetas en la misma primera prueba.')
para('La variable principal será la ganancia del ensemble bajo una política de contactos predefinida. Reportar adicionalmente ganancia individual, AUC, deltas pareados, victorias, tamaño, cobertura y costo. Como diagnóstico, puede añadirse una comparación a igual presupuesto de contactos fijado en agosto para todos: separa parte del efecto del ranking de la política de corte. Debe distinguirse de la métrica principal con corte propio.')
para('Antes de correr, preregistrar contrastes y una mejora mínima económicamente relevante acordada con Ale. No inventar retrospectivamente 5 % como condición. Si se exige inferencia estadística, fijar familia de contrastes, método y corrección por multiplicidad, reconociendo los períodos ya usados. Una regla económica favorable no es una prueba de generalización.')

page('9 Requisitos de reproducción y cierre')
para('La base del próximo prompt debe ser un contrato ejecutable versionado y validado contra su descripción, no una acumulación de instrucciones de distintas épocas. El mismo identificador debe vincular prompt, autorización, código, dataset, entorno, matrices, modelos, políticas y resultados. Ningún cambio posterior puede entrar silenciosamente en una corrida empezada.')
table(['Hito','Evidencia exigida para darlo por terminado'],[['Diseño congelado','Pregunta, brazos, fórmulas, máscaras, fuentes, meses, métricas, semillas, contrastes, presupuesto y criterio de cierre. Hash del contrato y commit.'],['Auditoría real','Claves únicas, tipos, clases, roturas, conteos de nulos por causa, filas y orden, nombres y orden de columnas, aliases, dimensiones y hashes de matrices.'],['Entorno','Python, bibliotecas y sistema efectivamente usados; configuración resuelta de LightGBM; archivos de dependencias reproducibles.'],['Ajustes','Los 10 trials de cada brazo, estado, parámetros, AUC, árboles y tiempos; selección comprobable del mejor; modelos por semilla con hash.'],['Congelamiento','Modelos, predicciones de agosto y proporciones por semilla y ensemble. Validación del hash antes de abrir octubre.'],['Evaluación','Regenerar agosto desde modelos, comparar predicciones; puntuar octubre sin reentrenar; comprobar cortes y aciertos con la identidad económica.'],['Respaldo','Git público con agregados y código; almacenamiento privado duradero de dataset, modelos y predicciones con ubicación, hashes y prueba de recuperación.'],['Reproducción independiente','Reconstruir desde el mismo dataset en otra máquina y comparar columnas, trials, árboles, predicciones y métricas. Registrar tolerancias antes de comparar.']],[1.3,5.57],size=9.5)
para('La auditoría complementaria de v4 cerró tres dudas: recuperó calibrar.py con el hash original, confirmó que los 25 modelos ya tenían SHA256 y recuperó las cinco listas ordenadas de columnas de octubre con igualdad del hash del protocolo completo. Por lo tanto, las afirmaciones anteriores de ausencia de esos elementos quedaron superadas. Siguen pendientes la recuperación y respaldo privado verificable de los archivos de modelos, evidencia histórica de Python/scikit-learn y una réplica integral del entrenamiento. No se debe afirmar “reproducido” por pasar un manifiesto.')
para('V5/v6 guardan entorno, parámetros, columnas y hashes privados más completos. V6 verificó 55 predicciones de agosto con error máximo cero antes de octubre. Eso valida la reutilización de esos modelos y matrices; no equivale a reproducir los 165 ajustes en otro equipo. La existencia de un hash tampoco acredita que el artefacto privado sea recuperable hoy.')
para('Para el próximo experimento: pruebas de huecos temporales, nulos, ceros, signos, fórmulas, selección solo en entrenamiento, empates, alineación de clientes, corte, reinicio y bloqueo de octubre; supervisor con límite medido y apagado verificado; recuperación de agregados antes del apagado. No publicar datos individuales ni credenciales. El cierre debe informar completos, parciales y pendientes, sin ocultar negativos.')

# Model cards
DESC={('v4','B0'):'Actuales + lag1/2 + delta1/2; control de historia corta.',('v4','F1'):'B0 + promedio, mínimo, máximo y rango W3.',('v4','F3'):'B0 + relativos frente a media W3, lag1 y lag2.',('v4','F4a'):'B0 + ranking transversal actual de las fuentes revisadas.',('v4','F4b'):'F4a + lag1/2, delta1/2, media, mínimo, máximo y rango W3 del ranking.',('v5','B0'):'Actuales + lag1/2 + delta1/2; control recalculado de v5.',('v5','L'):'Actuales + lag1/2; se retiran los deltas.',('v5','P'):'B0 + promedio W3.',('v5','MIN'):'B0 + mínimo W3.',('v5','MAX'):'B0 + máximo W3.',('v5','RANGO'):'B0 + máximo menos mínimo W3.',('v5','F1'):'B0 + promedio, mínimo, máximo y rango W3.',('v6','B0_J'):'Actuales + lag1/2 + delta1/2; control depurado en junio.',('v6','L4'):'B0_J + lag3; historia directa de hasta cuatro observaciones.',('v6','L6'):'L4 + lag4 y lag5; hasta seis observaciones.'}
for a in ['S3','S4','S6']:DESC['v6',a]='B0_J + media, mínimo, máximo y rango W'+a[1]+'. Pares comunes entre S3/S4/S6.'
for a in ['T4','T6']:DESC['v6',a]='B0_J + pendiente OLS W'+a[1]+'. Pares comunes entre T4/T6.'
for a in ['R3','R4','R6']:DESC['v6',a]='B0_J + relativos frente a media W'+a[1]+', lag1 y lag'+str(int(a[1])-1)+'. Pares comunes R3/R4/R6.'
for i,m in enumerate(models):
 if i%2==0:
  page('Anexo de modelos '+str(i+1)+(' a '+str(i+2) if i+1<len(models) else ''))
  para('Ganancias en M. AUC del ensemble. Δ frente al control de la misma versión. Parámetros completos y resultados individuales en los archivos de apoyo.')
 heading(m['version']+' '+m['arm'],2)
 a=m['august'];g=a['ensemble_gain'];s=m['summary'];o=m['october'];hp=m['best']['params'];best=m['best']
 if m['arm']==m['base']:verdict='Control; no se aplica promoción.'
 elif m['version']=='v4':verdict='No cumple promoción por AUC. Ganancia económica informada descriptivamente.'
 else:verdict=('Cumple' if m['eligible'] else 'No cumple')+' la regla económica de agosto; no es significancia estadística.'
 seedtext='101, 211, 307, 401, 503' if m['version']=='v4' else '211, 307, 401, 503, 601'
 train='marzo–junio; 507.328 filas' if m['version']!='v6' else 'junio; 128.474 filas'
 rows=[['Representación',DESC[m['version'],m['arm']]],['Diseño',f'{m["columns"]} columnas; train {train}; control {m["base"]}.'],['Ajuste propio',f'10 trials + 5 semillas ({seedtext}). Trial elegido {best["trial"]} (índice desde 0); {best["rounds"]} árboles; AUC Optuna {fmt(best["auc"],6)}.'],['Hiperparámetros',f'num_leaves={hp["num_leaves"]}; min_data_in_leaf={hp["min_data_in_leaf"]}; learning_rate={fmt(hp["learning_rate"],8)}; feature_fraction={fmt(hp["feature_fraction"],8)}; bagging_fraction={fmt(hp["bagging_fraction"],8)}.'],['Agosto ensemble',f'AUC {fmt(a["ensemble_auc"],6)}; G suavizada {mil(g["smoothed_gain_max"])}; Δ {mil(s["ensemble_delta"],True)}; G puntual {mil(g["point_gain_at_cut"])}.'],['Agosto corte',f'{g["cut_contacts"]} contactos ({fmt(100*g["contact_proportion"],4)} %); {g["hits_recalculated"]} aciertos BAJA+2 en el corte.'],['Agosto semillas',f'G media {mil(st.mean(x["gain"]["smoothed_gain_max"] for x in a["seeds"]))}; Δ medio {mil(s["gain_delta_mean"],True)}; DE Δ {mil(s["gain_delta_sd"])}; victorias {s["gain_wins"]}/5. Δ AUC medio {fmt(s["auc_delta_mean"],6,True)}.']]
 if o:
  og=o['ensemble_gain'];os=o['summary'];rows +=[['Octubre ensemble',f'AUC {fmt(o["ensemble_auc"],6)}; G {mil(og["point_gain"])}; Δ {mil(os["ensemble_delta"],True)} ({fmt(os["ensemble_delta_pct"],3,True)} %); {og["cut_contacts"]} contactos y {og["hits_recalculated"]} aciertos.'],['Octubre semillas',f'G media {mil(os["gain_mean"])}; Δ medio {mil(os["gain_delta_mean"],True)}; DE Δ {mil(os["gain_delta_sd"])}; victorias {os["wins"]}/5.']]
 else:rows +=[['Octubre','Pendiente. No se extrapola la ganancia de agosto ni se imputa cero.']]
 if m['arm']==m['base']:
  rows=[(label,value.replace('victorias 0/5','victorias no aplica')) for label,value in rows]
 rows +=[['Decisión y fuente',verdict+' Fuente '+m['version'].upper()+'/'+m['arm']+'; características comunes en secciones 2 y 3.']]
 table(['Característica','Valor observado'],rows,[1.25,5.62],size=9)

page('10 Contrastes de profundidad adicionales de v6')
para('Estos contrastes fueron registrados antes de correr v6. No basta con que dos brazos ganen contra B0_J para afirmar que el de mayor ventana supera al menor. La tabla conserva diferencias directas, sin cambiar retrospectivamente el control. La regla de agosto se aplica al contraste pertinente.')
rows=[]
for c in D['versions']['v6']['final']['comparisons']:
 if c['control']=='B0_J':continue
 oc=next(x for x in D['october_v6_contrasts'] if x['arm']==c['arm'] and x['control']==c['control'])
 rows.append([c['arm']+' − '+c['control'],mil(c['ensemble_gain_delta'],True),str(c['gain_wins'])+'/5',mil(oc['ensemble_gain_delta'],True),str(oc['gain_wins'])+'/5','Sí' if c['eligible_by_operational_gain_rule'] else 'No'])
table(['Contraste','Δ ago M','Gana ago','Δ oct M','Gana oct','Regla ago'],rows,[1.25,1.2,.9,1.2,.9,1.32])
para('El signo entre meses puede cambiar. En particular, el mejor R4 en octubre no elimina el mejor R3 en agosto, y extender tendencia de W4 a W6 no dio una mejora económica consistente. Las cifras representan cada receta con su búsqueda propia y la política de cobertura congelada, no una prueba causal sobre cualquier cliente y cualquier mes.')
heading('Lectura para el próximo prompt',2)
para('Cada nueva hipótesis debe nombrar un control directo antes de correr. Una unión debe compararse con sus componentes; una poda con su conjunto completo; un cambio de máscara con la misma fórmula; un cambio de longitud con pares fuente–fórmula comparables. Si cambian varias condiciones a la vez, el resultado debe describirse como el efecto del paquete, no como el efecto aislado de una de ellas.')

page('11 Fuentes y archivos que acompañan el informe')
para('La fuente de verdad de los números es cada result.json por brazo y semilla, contrastada con FINAL.json, best.json, trials.json, contratos y políticas congeladas. Se verificaron 23 brazos, diez trials y cinco semillas por brazo, elección del mejor AUC, diferencias pareadas y cortes de octubre. Los aciertos se recalcularon con la identidad económica y son enteros. Los nombres y cantidades de columnas se cotejaron para los 23 brazos; para v4 se usó el protocolo completo recuperado en auditoria_trazabilidad_2026-11-13.')
para('Repositorio propio consultado: ClariRZ/Experimentos-, commit '+D['source_commit']+'. Los estados de los documentos históricos se conservan; las fechas de carpetas no sustituyen la identidad de corrida.')
sources=[('P4','experimento_2026-11-13/prompts/','Original, plan adaptado y contrato ejecutado.'),('P5','HISTORIA_2019_01/v5/prompts/PROMPT_MAESTRO_HISTORIA_2019_v5.md','Prompt maestro v5; la corrida cubrió su primera etapa.'),('P6','HISTORIA_2019_01/v6/prompts/PROMPT_MAESTRO_HISTORIA_2019_v6.md','Prompt maestro v6 y rama de profundidad.'),('V4','experimento_2026-11-13/resultados/','Agosto por brazo y FINAL de octubre; código original y README en la carpeta raíz del experimento.'),('V5','HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01/','Config, columnas, trials, best y result por brazo. Sin octubre.'),('V6','HISTORIA_2019_01/v6/resultados/v6_20261113_02/','Config, columnas, trials, best y result por brazo.'),('O6','HISTORIA_2019_01/v6/resultados/octubre_v6_01/','Política congelada, verificación de agosto y resultados de octubre.'),('A4','auditoria_trazabilidad_2026-11-13/','Cierre de calibrador, hashes de modelos y listas completas de columnas de v4.')]
for code,path,desc in sources:
 para(code+' — '+desc)
 p=doc.add_paragraph('https://github.com/ClariRZ/Experimentos-/tree/'+D['source_commit']+'/'+path)
 for r in p.runs:r.font.size=Pt(8)
 md.append('https://github.com/ClariRZ/Experimentos-/tree/'+D['source_commit']+'/'+path+'\n')
para('Tutoría de Ale: transcripción y mensaje de Zulip aportados por Clara en esta conversación. No se atribuyen a Ale los conteos de brazos, diez trials, cinco semillas ni nuestras reglas de promoción. Las fórmulas concretas ejecutadas se contrastan con fe_core.py; no con el nombre informal de una variable en una lámina.')
para('Comparación externa: ezequielabregu/DMEyF-2026-experi-colab-feature_historico, commit 770abaa9cad412647211c255360cb6dfe364e697; pipeline/parametros.py, pipeline/funciones.py, pipeline/README.md y resultados/pipeline/main_comparacion.csv.')
para('Archivos de apoyo: evidencia.json con parámetros sin redondeo, métricas y listas disponibles; modelos_resumen.csv y semillas.csv con métricas agregadas no identificables; prompts_originales con copias exactas; fuentes_sha256.json con procedencia; scripts de extracción y de redacción; manifiesto de integridad de la entrega. Las cifras impresas se redondean solo para lectura.')

OUT.joinpath('Informe_prompts_modelos_hipotesis_2019.docx').parent.mkdir(exist_ok=True,parents=True)
doc.save(OUT/'Informe_prompts_modelos_hipotesis_2019.docx');(OUT/'INFORME.md').write_text('\n'.join(md))
shutil.copy2(W/'evidencia.json',OUT/'evidencia.json')
with (OUT/'modelos_resumen.csv').open('w') as f:
 fields=['version','arm','columns','auc_august','gain_august_smoothed','gain_august_point','delta_august_ensemble','wins_august','eligible_original','gain_october','delta_october_ensemble','wins_october'];writer=csv.DictWriter(f,fields);writer.writeheader()
 for m in models:
  a=m['august'];o=m['october'];writer.writerow(dict(version=m['version'],arm=m['arm'],columns=m['columns'],auc_august=a['ensemble_auc'],gain_august_smoothed=a['ensemble_gain']['smoothed_gain_max'],gain_august_point=a['ensemble_gain']['point_gain_at_cut'],delta_august_ensemble=m['summary']['ensemble_delta'],wins_august=m['summary']['gain_wins'],eligible_original=m['eligible'],gain_october=o['ensemble_gain']['point_gain'] if o else '',delta_october_ensemble=o['summary']['ensemble_delta'] if o else '',wins_october=o['summary']['wins'] if o else ''))
with (OUT/'semillas.csv').open('w') as f:
 fields=['version','arm','month','seed','auc','smoothed_gain','point_gain','cut_contacts'];writer=csv.DictWriter(f,fields);writer.writeheader()
 for m in models:
  for month,key in [(201908,'august'),(201910,'october')]:
   if not m[key]:continue
   for s in m[key]['seeds']:
    g=s['gain'];writer.writerow(dict(version=m['version'],arm=m['arm'],month=month,seed=s['seed'],auc=s['auc'],smoothed_gain=g.get('smoothed_gain_max',''),point_gain=g.get('point_gain_at_cut',g.get('point_gain')),cut_contacts=g['cut_contacts']))
(OUT/'fuentes_sha256.json').write_text(json.dumps({'commit':D['source_commit'],'files':D['source_files_sha256']},ensure_ascii=False,indent=2)+'\n')
print('Documento y tablas generados',len(models),'modelos')

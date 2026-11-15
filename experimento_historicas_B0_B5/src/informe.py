"""Informe HTML autónomo y gráficos, sólo a partir de resultados reales finalizados."""
import argparse,base64,html,json,re
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--out',required=True);a=p.parse_args()
rdir=Path(a.results);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
assert (rdir/'EVALUATED.json').exists(),'No hay evaluación real terminada'
r=pd.read_csv(rdir/'resultados.csv');assert len(r)==6
cfg=json.loads((out/'config.json').read_text())
search=pd.DataFrame([{'Parámetro':k,'Mínimo':v[0],'Máximo':v[1],'Escala':'logarítmica' if k in ['num_leaves','learning_rate','min_data_in_leaf'] else 'uniforme'} for k,v in cfg['search_space'].items()])
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
colors=['#65748c','#5592a8','#0b6e69','#99b94d','#bf8d39','#9364a4']
fig,ax=plt.subplots(figsize=(10,5))
ax.bar(r.experimento,r.ganancia_octubre/1e6,color=colors)
ax.axhline(r.loc[r.experimento=='B2','ganancia_octubre'].iloc[0]/1e6,color='#0b6e69',ls='--',label='Referencia de Ale (B2)')
ax.set(ylabel='Ganancia (millones de pesos)',title='Octubre: política de contactos fijada en agosto');ax.legend();fig.tight_layout();fig.savefig(out/'ganancias.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,4.8))
for i,e in enumerate(r.experimento):
 c=pd.read_csv(rdir/e/'curva_octubre.csv');limit=int(.2*(len(c)-1));k=int(r.loc[r.experimento==e,'contactos'].iloc[0])
 for ax,sub in [(axs[0],c),(axs[1],c.iloc[:limit+1])]:
  ax.plot(sub.contactos,sub.ganancia/1e6,color=colors[i],label=e)
  if k<=sub.contactos.iloc[-1]:ax.scatter([k],[c.ganancia.iloc[k]/1e6],color=colors[i],s=25)
  ax.set(xlabel='Clientes contactados',ylabel='Ganancia acumulada (millones)');ax.legend(ncol=3,fontsize=9)
axs[0].set_title('Curva completa');axs[1].set_title('Detalle: primer 20 % de clientes')
fig.suptitle('Curvas descriptivas; puntos = política fijada previamente');fig.tight_layout();fig.savefig(out/'curvas.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4))
ax.bar(r.experimento.iloc[1:],r.delta_anterior.iloc[1:]/1e6,color=colors[1:]);ax.axhline(0,color='#333',lw=1);ax.set(ylabel='Cambio de ganancia (millones)',title='Aporte observado respecto del paso anterior');fig.tight_layout();fig.savefig(out/'incrementos.png',dpi=150);plt.close(fig)

def embed(name):return '<img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/name).read_bytes()).decode()+'">'
best=r.loc[r.ganancia_octubre.idxmax()];b0=r.iloc[0];b2=r.iloc[2];best_auc=r.loc[r.auc_agosto.idxmax()];best_common=r.loc[r.ganancia_presupuesto_comun_B2.idxmax()]
families={'B0':'Originales','B1':'+ lags 1 y 2','B2':'+ deltas 1 y 2 (Ale)','B3':'+ medias de 3 meses','B4':'+ pendientes de 3 meses','B5':'+ ratios 1 y 2'}
plan=pd.DataFrame([{'experimento':e,'familia_agregada':families[e],'columnas':int(r.loc[r.experimento==e,'variables'].iloc[0])} for e in r.experimento])
display=r[['experimento','variables','auc_agosto','ganancia_octubre','contactos','aciertos_BAJA2','delta_anterior','delta_B0','delta_B2']].copy()
for c in display:
 if c=='auc_agosto':display[c]=display[c].map(lambda x:f'{x:.6f}')
 elif c not in ['experimento']:display[c]=display[c].map(lambda x:'—' if pd.isna(x) else f'{x:,.0f}')
display=display.rename(columns={'experimento':'Modelo','variables':'Variables','auc_agosto':'AUC agosto','ganancia_octubre':'Ganancia octubre ($)','contactos':'Contactos','aciertos_BAJA2':'Aciertos BAJA+2','delta_anterior':'Diferencia anterior ($)','delta_B0':'Diferencia B0 ($)','delta_B2':'Diferencia B2 ($)'})
cost=r[['experimento','segundos','pico_ram_mib_proceso','arboles','trials']].copy()
cost['segundos']=cost['segundos'].round(1);cost['pico_ram_mib_proceso']=cost['pico_ram_mib_proceso'].round(1)
cost=cost.rename(columns={'experimento':'Modelo','segundos':'Segundos','pico_ram_mib_proceso':'Pico RAM proceso (MiB)','arboles':'Árboles','trials':'Evaluaciones'})
interpret=[]
for i,row in r.iterrows():
 if i==0:continue
 sign='aumentó' if row.delta_anterior>0 else 'disminuyó' if row.delta_anterior<0 else 'no cambió'
 interpret.append(f"<li><b>{row.experimento} ({html.escape(families[row.experimento])}):</b> la ganancia {sign} en {abs(row.delta_anterior):,.0f} pesos respecto del paso anterior. Es un aporte condicionado a las familias previas y a la optimización de cada configuración.</li>")
source=json.loads((out/'auditoria'/'repositorio.json').read_text())
coverage=pd.read_csv(out/'auditoria'/'cobertura_familias.csv').pivot(index='familia',columns='particion',values='cobertura_pct').round(2)
conclusions=''.join('<p>'+html.escape(t)+'</p>' for t in (out/'conclusiones.txt').read_text().split('\n\n')[1:])
source_analysis=''.join('<p>'+html.escape(t)+'</p>' for t in (out/'analisis_del_material.txt').read_text().split('\n\n'))
common=r[['experimento','contactos_comunes','ganancia_presupuesto_comun_B2']].rename(columns={'experimento':'Modelo','contactos_comunes':'Contactos','ganancia_presupuesto_comun_B2':'Ganancia ($)'})
for col in ['Contactos','Ganancia ($)']:common[col]=common[col].map(lambda x:f'{x:,.0f}')
comparison=pd.read_csv(out/'marcelo_usar_adaptar_excluir.csv').to_html(index=False,escape=True)
report=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Experimento de variables históricas</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:1120px;margin:40px auto;padding:0 24px;color:#20303d}}h1,h2{{color:#0b6e69}}h1{{font-size:34px}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{border-bottom:1px solid #d9e2e5;padding:9px;text-align:right}}td:first-child,th:first-child{{text-align:left}}th{{background:#edf4f4}}img{{max-width:100%;height:auto}}.note{{background:#f0f5f5;padding:18px;border-left:4px solid #0b6e69}}code{{overflow-wrap:anywhere}}@media print{{body{{margin:10mm;font-size:11px}}h2{{break-after:avoid}}img,table{{break-inside:avoid}}}}</style>
<h1>¿Cuánto aporta la historia del cliente?</h1><p>Experimento acumulativo B0–B5 · Datos de 2019 · Reglas económicas 2026</p>
<p class="note">La mayor ganancia observada fue la de <b>{best.experimento}</b>: <b>{best.ganancia_octubre:,.0f} pesos</b>, con {best.contactos:,.0f} contactos. Es la mejor observada entre seis configuraciones evaluadas sobre un único mes; no constituye una nueva evaluación independiente de un ganador seleccionado posteriormente.</p>
<h2>1. Hipótesis</h2><p>Incorporar valores pasados, cambios absolutos, niveles recientes, pendientes y cambios relativos puede mejorar la predicción respecto de originales. B2 representa el baseline de Ale; B0 permite cuantificar el aporte total de las históricas.</p>
<h2>2. Diseño experimental</h2>{plan.rename(columns={'experimento':'Modelo','familia_agregada':'Familia incorporada','columnas':'Columnas acumuladas'}).to_html(index=False,escape=True)}<p>Entrenamiento completo de marzo a junio de 2019 (506.871 filas), validación agosto (131.775), test octubre (135.633). Etiquetas construidas únicamente con presencia hasta diciembre de 2019. Como la base no traía clase_ternaria, BAJA+1 se define por ausencia en el mes siguiente; BAJA+2 por presencia en el siguiente y ausencia en el segundo; CONTINUA por presencia en ambos. Noviembre queda parcialmente censurado y diciembre sin clase; no se incorporan como filas de entrenamiento ni evaluación. Positivos para entrenamiento y AUC: BAJA+1 o BAJA+2. Sin sampling y sin usar otros años.</p>
<p>LightGBM, {cfg['trials']} evaluaciones por configuración con Optuna TPE ({cfg['startup_trials']} iniciales), AUC para selección y early stopping de {cfg['early_stopping']} rondas, máximo {cfg['max_rounds']} árboles. Semilla {cfg['seed']}. La búsqueda tiene presupuesto limitado y no garantiza el óptimo global. Cada familia se calcula sobre columnas originales, sin transformaciones recursivas.</p>
<details><summary>Espacio de búsqueda y parámetros fijos</summary>{search.to_html(index=False)}<p>bagging_freq=1, max_bin=255, feature_pre_filter=False, deterministic=True, force_col_wise=True; ocho hilos. Los cinco primeros ensayos son exploratorios y los quince restantes usan TPE. Cada configuración tiene su estudio propio.</p></details><p>Ganancia: +1.072.500 por BAJA+2 contactado; −27.500 por otro contacto. Equivalente a 1.100.000 × aciertos −27.500 × contactos. Sin reescalado public/private.</p>
<p>El número de contactos maximiza ganancia en agosto, incluyendo cero; se transfiere la proporción a octubre. Empates de ranking: identificador ascendente; empate de ganancia: menos contactos. Se reutiliza agosto para hiperparámetros y política, limitación reconocida. Se congelaron modelos, políticas y configuración antes de abrir los resultados del test.</p>
<p>Ventanas de tres meses incluyen el actual, mínimo dos valores válidos. Lags por mes calendario exacto. Identificador y foto_mes excluidos como predictores. Categorías codificadas sólo con entrenamiento; fechas originales y lags, sin aritmética histórica adicional. Detalle de elegibilidad en manifest.json.</p>
<p>Fórmulas: lag<sub>k</sub> = x<sub>t−k</sub>; delta<sub>k</sub> = x<sub>t</sub> − x<sub>t−k</sub>, para k=1,2. Media3 promedia valores válidos de t−2,t−1,t. Pendiente3 ajusta una recta a esos valores usando meses calendario como eje. Ratio<sub>k</sub> = x<sub>t</sub>/x<sub>t−k</sub>; denominador cero o faltante produce faltante, sin constantes artificiales. Se conserva el valor cero original.</p><h2>3. Resultados</h2>{display.to_html(index=False,escape=True)}{embed('ganancias.png')}{embed('incrementos.png')}
<p>La tabla presenta ganancia con la política fijada previamente, no el máximo elegido a posteriori en octubre. El CSV incluye una evaluación secundaria con presupuesto común de contactos fijado por B2.</p>
<h3>Comparación con presupuesto común fijado por B2</h3>{common.to_html(index=False,escape=True)}<h3>Cobertura de cada familia</h3>{coverage.to_html()}<p>Porcentaje de celdas con valores finitos, calculado sólo en desarrollo. Los ratios tienen menor cobertura porque muchos denominadores son cero. No se descartan clientes por estos faltantes.</p><h3>Costo y tamaño de los modelos</h3>{cost.to_html(index=False,escape=True)}<p>RAM: pico acumulado del proceso en MiB, no medición aislada de cada modelo. Tiempos por invocación de entrenamiento y selección, sin incluir transferencia ni preparación de variables. El costo por ensayo queda registrado en trials.csv.</p><h2>4. Interpretación y limitaciones</h2>{conclusions}
<p>B1 incorpora observaciones históricas nuevas respecto de B0. B2–B5 reorganizan los mismos valores del mes actual y sus dos lags: pueden facilitar los cortes de los árboles, pero no amplían el horizonte ni incorporan datos externos. Con tres meses completos, pendiente3 = delta2/2. Por ello, B4 puede ser redundante y su efecto no debe interpretarse automáticamente como nueva información. Ventanas incompletas y distintas representaciones pueden cambiar el entrenamiento.</p>
<p>AUC y ganancia responden a preguntas diferentes: el AUC usa BAJA+1 y BAJA+2 combinadas y considera el ranking global; la ganancia premia sólo BAJA+2 dentro del grupo contactado. Por eso una mejora de AUC no garantiza una mejora económica.</p><p>Los modelos tienen hiperparámetros optimizados por separado. El efecto depende del orden de las familias y de la optimización. Se completó el diseño acumulativo; no se ejecutaron las comparaciones independientes opcionales. Se utilizó una única semilla y un único mes de test: no se estableció significancia estadística ni estabilidad temporal. La importancia de variables es descriptiva, no prueba causal de mejora.</p>
<p>tmobile_app y cmobile_app_trx están completamente faltantes en los meses de entrenamiento. Se conservan por consistencia del diseño, pero no pueden aportar señal aprendida en este protocolo; la cantidad de columnas de entrada no equivale a cantidad de variables efectivamente usadas en los árboles.</p><p>La ganancia es una métrica económica del ejercicio, no una medición de ingresos efectivamente obtenidos en una campaña real.</p>
<h2>5. Curvas descriptivas de octubre</h2>{embed('curvas.png')}<p>Los máximos de estas curvas son retrospectivos y no se usan para redefinir la política.</p>
<h2>6. Material de Marcelo: usos y exclusiones</h2>{comparison}<details><summary>Reconstrucción detallada y límites de la evidencia</summary>{source_analysis}</details>
<h2>7. Qué seguir experimentando</h2><p>Validar estabilidad en otros meses bajo un nuevo protocolo temporal; repetir semillas; contrastar medias, pendientes y ratios contra B2 de forma independiente; ampliar la búsqueda sólo antes de abrir un nuevo test. Los resultados actuales no justifican afirmar que una familia funcione o falle universalmente.</p>
<h2>8. Reproducibilidad y fuentes</h2><p>Parquet original: <code>competencia_02_crudo.parquet</code>. SHA-256: <code>84dffddadf9216be9460793ea3c28d87bff82b3c194a67a2e49fc7b4a7475a22</code>. VM clari-c1-fundados, 8 CPU, 62 GiB aproximados de RAM. Las pruebas sintéticas verifican código y no integran los resultados de esta tabla.</p>
<ul><li>Pautas de Ale proporcionadas por la usuaria.</li><li><a href="https://github.com/ClariRZ/dmeyf2026/blob/{source['commit']}/zero2hero/zero2hero_01.ipynb">Repositorio 2026: función de ganancia, commit {source['commit']}</a>.</li><li>PDF local «Data Mining en Economía y Finanzas (EyF)», pp. 438–439, 474–475, 779–780 y 853–856. Compilación de clases/anotaciones: atribuciones individuales limitadas.</li></ul>
<p>Archivos complementarios: config.json, resultados/resultados.csv, resultados/FROZEN.json, manifiesto de variables, auditoría, código y versiones de dependencias.</p></html>'''
if 'data_sha256' not in cfg:
 report=report.replace('<h1>', '<p><b>PRUEBA INTERNA DE FORMATO CON DATOS SINTÉTICOS. NO ES UN RESULTADO DEL EXPERIMENTO.</b></p><h1>',1)
# Separador de miles en el texto visible; no modificar CSS, enlaces ni imágenes.
report=''.join(re.sub(r'\d{1,3}(?:,\d{3})+',lambda m:m.group().replace(',','.'),part) if not part.startswith('<') else part for part in re.split(r'(<[^>]+>)',report))
(out/'informe.html').write_text(report)
script=f'''GUION PROPUESTO — VIDEO GRUPAL (aproximadamente 4–5 minutos)

1. HIPÓTESIS (35 segundos)
Queríamos medir cuánto aporta la historia de cada cliente. Partimos de originales y agregamos una familia por vez. La pregunta no era si más columnas siempre ayudan, sino qué mejora observamos respecto del paso anterior y de la referencia de Ale.

2. DISEÑO (75 segundos)
Entrenamos con marzo a junio de 2019, sin sampling. Validamos en agosto y reservamos octubre para la comparación final. B0 usa originales; B1 agrega lags; B2 agrega deltas y coincide con la referencia de Ale; B3 medias; B4 pendientes; B5 ratios. Optimizamos cinco hiperparámetros por AUC con el mismo presupuesto. Los contactos se fijaron con agosto y la regla se congeló antes de octubre. La ganancia usa los importes de 2026.

3. RESULTADOS (90 segundos)
Mostrar la tabla y el gráfico de ganancia. B0 obtuvo {b0.ganancia_octubre:,.0f} pesos y B2 {b2.ganancia_octubre:,.0f}. La mayor ganancia observada fue {best.experimento}: {best.ganancia_octubre:,.0f} pesos con {best.contactos:,.0f} contactos. Explicar las diferencias incrementales del gráfico sin confundirlas con efectos independientes del orden. Con 5.042 contactos para todos, B2 y B3 empataron; B4 obtuvo la mayor ganancia, por un acierto adicional. La ventaja de B3 con su política individual combina seis aciertos menos con 331 contactos menos. Por eso no afirmamos que su ranking sea superior al de B2 a cualquier presupuesto. B4 perdió ganancia con su política individual y B5 recuperó parte de esa caída, sin superar a B3.

4. LIMITACIONES Y CONCLUSIONES (60 segundos)
Evaluamos un mes de test y una semilla: no afirmamos estabilidad general. La pendiente con tres meses completos es delta2 dividido dos, por lo que puede ser redundante. Cada conjunto se optimizó por separado. El material de Marcelo orientó las transformaciones, pero no usamos sus importes, sampling ni cortes heredados. Seguiríamos con pruebas independientes contra B2, más semillas y nuevos meses fuera de muestra.

Bibliografía: compartir junto al video el repositorio y commit indicados en el informe, las pautas de Ale y el PDF consultado. No presentar resultados sintéticos ni máximos retrospectivos como ganancia de una decisión fijada antes del test.
'''
script=re.sub(r'\d{1,3}(?:,\d{3})+',lambda m:m.group().replace(',','.'),script)
(out/'guion_video.txt').write_text(script)
print('Informe y guion generados; procedencia: '+('experimento' if 'data_sha256' in cfg else 'prueba sintética de formato'))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta

# Datos proporcionados
data = {
    'Month': ['jun-26', 'sep-26', 'oct-26', 'nov-26', 'dic-26', 'ene-27', 'feb-27', 
              'mar-27', 'abr-27', 'may-27', 'jun-27', 'jul-27', 'ago-27', 'sep-27', 
              'oct-27', 'nov-27', 'dic-27'],
    'Payments To ING': [50000, 100000, 100000, 100000, 100000, 100000, 100000, 
                        455220, 455220, 179688, 179688, 179688, 179688, 179688, 
                        179688, 179688, 179688],
    'PSC Others': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 212500, 712500, 532500, 332500, 0, 0]
}

# Crear DataFrame
df = pd.DataFrame(data)

# Mapa de meses en español a número
meses_es = {
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
}

def month_to_date(month_str):
    """Convierte formato 'sep-26' a datetime (primer día del mes)"""
    parts = month_str.split('-')
    mes_abbr = parts[0].lower()
    year = int(parts[1]) + 2000
    return datetime(year, meses_es[mes_abbr], 1)

df['Date'] = df['Month'].apply(month_to_date)
df['Date_Next'] = df['Date'].shift(-1)
df.loc[df.index[-1], 'Date_Next'] = df.loc[df.index[-1], 'Date'] + timedelta(days=30)

# Colores corporativos INGECART
COLOR_ING = '#E84C22'      # Naranja INGECART
COLOR_PSC = '#87CEEB'      # Azul cielo
COLOR_FONDO = '#FFFFFF'    # Blanco

# Crear figura
fig, ax = plt.subplots(figsize=(14, 12))
fig.patch.set_facecolor(COLOR_FONDO)
ax.set_facecolor(COLOR_FONDO)

# Configuración de barras
bar_height = 0.65
y_pos = 0
y_positions_ing = []
y_positions_psc = []
labels_ing = []
labels_psc = []
values_ing = []
values_psc = []
start_dates_ing = []
start_dates_psc = []
duration_ing = []
duration_psc = []

# Recopilar datos para Payments To ING
for idx, row in df.iterrows():
    if row['Payments To ING'] > 0:
        start = row['Date']
        end = row['Date_Next']
        duration = (end - start).days
        y_positions_ing.append(y_pos)
        labels_ing.append(row['Month'])
        values_ing.append(row['Payments To ING'])
        start_dates_ing.append(start)
        duration_ing.append(duration)
        y_pos += 1

# Añadir espacio entre grupos
y_pos += 1  # Espacio fijo de 1 (entero)

# Recopilar datos para PSC Others
for idx, row in df.iterrows():
    if row['PSC Others'] > 0:
        start = row['Date']
        end = row['Date_Next']
        duration = (end - start).days
        y_positions_psc.append(y_pos)
        labels_psc.append(row['Month'])
        values_psc.append(row['PSC Others'])
        start_dates_psc.append(start)
        duration_psc.append(duration)
        y_pos += 1

# Dibujar barras para Payments To ING
for i, (y, start, duration, value) in enumerate(zip(y_positions_ing, start_dates_ing, duration_ing, values_ing)):
    ax.barh(y, duration, left=start, height=bar_height, 
            color=COLOR_ING, alpha=0.85, edgecolor='white', linewidth=0.5)
    
    # Formatear importe
    if value >= 1000000:
        text = f'${value/1000000:.1f}M'
    elif value >= 1000:
        text = f'${value/1000:.0f}K'
    else:
        text = f'${value:,.0f}'
    
    x_center = start + timedelta(days=duration/2)
    ax.text(x_center, y, text, ha='center', va='center', 
            fontsize=9, fontweight='bold', color='white', 
            bbox=dict(boxstyle='round,pad=0.3', facecolor=COLOR_ING, alpha=0.7, edgecolor='none'))

# Dibujar barras para PSC Others
for i, (y, start, duration, value) in enumerate(zip(y_positions_psc, start_dates_psc, duration_psc, values_psc)):
    ax.barh(y, duration, left=start, height=bar_height, 
            color=COLOR_PSC, alpha=0.85, edgecolor='white', linewidth=0.5)
    
    # Formatear importe
    if value >= 1000000:
        text = f'${value/1000000:.1f}M'
    elif value >= 1000:
        text = f'${value/1000:.0f}K'
    else:
        text = f'${value:,.0f}'
    
    x_center = start + timedelta(days=duration/2)
    ax.text(x_center, y, text, ha='center', va='center', 
            fontsize=9, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))

# Configurar eje Y - Versión SIMPLIFICADA y CORREGIDA
all_y = y_positions_ing + y_positions_psc

# Crear etiquetas de forma simple
y_labels = []
for label in labels_ing:
    y_labels.append(f'{label.upper()} (Pago ING)')
for label in labels_psc:
    y_labels.append(f'{label.upper()} (PSC Others)')

# Si hay menos etiquetas que posiciones, añadir espacios vacíos al final
while len(y_labels) < len(all_y):
    y_labels.append('')

ax.set_yticks(all_y)
ax.set_yticklabels(y_labels, fontsize=8)

# Configurar eje X
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=2))
plt.xticks(rotation=45, ha='right', fontsize=9)

# Línea vertical de hoy
today = datetime.now()
ax.axvline(x=today, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Actualidad')

# Títulos
ax.set_xlabel('MESES', fontsize=12, fontweight='bold', color='#333333')
ax.set_ylabel('PERIODO DE PAGO', fontsize=12, fontweight='bold', color='#333333')
ax.set_title('DIAGRAMA DE GANTT - CALENDARIO DE PAGOS\nPROYECTO BHS CORRUGATOR - PACIFIC SOUTHWEST PACKAGING', 
             fontsize=14, fontweight='bold', color=COLOR_ING, pad=20)

ax.grid(axis='x', alpha=0.2, linestyle='--')
ax.set_ylim(-0.5, max(all_y) + 0.8 if all_y else 10)

# Leyenda
legend_elements = [
    mpatches.Patch(color=COLOR_ING, alpha=0.85, label='Payments To INGECART (Pagos a INGECART)'),
    mpatches.Patch(color=COLOR_PSC, alpha=0.85, label='PSC Others (Pagos a Terceros)')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10, frameon=True, fancybox=True)

# Información adicional
info_text = "INGECART - Turnkey Project BHS Relocation\nUSA - Visalia, California"
ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=8,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))

plt.tight_layout()
plt.savefig('gantt_payments_ingecart.png', dpi=200, bbox_inches='tight', facecolor=COLOR_FONDO)
print("✅ Gráfico guardado como 'gantt_payments_ingecart.png'")
plt.show()

# Resumen
print("\n" + "="*80)
print("RESUMEN DE PAGOS - PROYECTO BHS CORRUGATOR")
print("="*80)

total_ing = df['Payments To ING'].sum()
total_psc = df['PSC Others'].sum()
total_general = total_ing + total_psc

print(f"\n💰 Total Pagos a INGECART:     ${total_ing:>15,.2f}")
print(f"🏭 Total Pagos a Terceros:    ${total_psc:>15,.2f}")
print(f"📦 TOTAL GENERAL PROYECTO:     ${total_general:>15,.2f}")

print("\n" + "-"*80)
print("Pagos a INGECART por año:")
for year in ['2026', '2027']:
    yearly = df[df['Month'].str.contains(year.lower())]['Payments To ING'].sum()
    print(f"  {year}: ${yearly:>15,.2f}")

print("\n" + "-"*80)
print("Pagos a Terceros (PSC Others) por año:")
for year in ['2027']:
    yearly = df[df['Month'].str.contains(year.lower())]['PSC Others'].sum()
    print(f"  {year}: ${yearly:>15,.2f}")

print("\n" + "="*80)
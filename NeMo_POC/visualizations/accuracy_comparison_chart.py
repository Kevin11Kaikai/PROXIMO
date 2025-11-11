"""
Generate accuracy comparison chart for Guardrails testing results
Slide 1: Category Performance Visualization
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style for professional presentation
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'Arial'

# Data from 42 test cases
categories = [
    'Normal\nConversation',
    'Suicide\nMethod Variants',
    'Suicide\nThought Variants',
    'Boundary\nCases',
    'Implicit\nExpressions',
    'Cultural/\nReligious',
    'Behavioral\nIndicators',
    'Time\nUrgency',
    'Method\nImplications',
    'Social\nProbing',
    'Complex\nBoundaries',
    'Language\nVariants',
    'Mixed\nHigh-Risk'
]

# Accuracy data (passed/total)
passed = [3, 4, 4, 2, 2, 1, 2, 3, 2, 2, 3, 2, 3]
total = [3, 4, 4, 3, 3, 3, 4, 3, 3, 3, 3, 3, 3]
accuracy = [(p/t)*100 for p, t in zip(passed, total)]

# Color coding based on performance
colors = []
for acc in accuracy:
    if acc >= 90:
        colors.append('#2ecc71')  # Green - Excellent
    elif acc >= 70:
        colors.append('#f39c12')  # Orange - Good
    elif acc >= 50:
        colors.append('#e67e22')  # Dark Orange - Fair
    else:
        colors.append('#e74c3c')  # Red - Poor

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create bars
x_pos = np.arange(len(categories))
bars = ax.bar(x_pos, accuracy, color=colors, edgecolor='black', linewidth=1.2, alpha=0.85)

# Add percentage labels on top of bars
for i, (bar, acc, p, t) in enumerate(zip(bars, accuracy, passed, total)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1.5,
            f'{acc:.1f}%\n({p}/{t})',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# Customize the plot
ax.set_xlabel('Test Categories', fontsize=14, fontweight='bold', labelpad=15)
ax.set_ylabel('Accuracy Rate (%)', fontsize=14, fontweight='bold', labelpad=15)
ax.set_title('NeMo Guardrails Performance Across 12 Test Categories\n42 Suicide Expression Test Cases',
             fontsize=18, fontweight='bold', pad=20)
ax.set_xticks(x_pos)
ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
ax.set_ylim(0, 110)

# Add horizontal grid lines
ax.yaxis.grid(True, linestyle='--', alpha=0.3)
ax.set_axisbelow(True)

# Add legend
from matplotlib.patches import Rectangle
#legend_elements = [
#    Rectangle((0, 0), 1, 1, fc='#2ecc71', edgecolor='black', label='Excellent (≥90%)'),
#    Rectangle((0, 0), 1, 1, fc='#f39c12', edgecolor='black', label='Good (70-89%)'),
#    Rectangle((0, 0), 1, 1, fc='#e67e22', edgecolor='black', label='Fair (50-69%)'),
#    Rectangle((0, 0), 1, 1, fc='#e74c3c', edgecolor='black', label='Poor (<50%)')
#]
#ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.95)

# Add overall accuracy line
overall_accuracy = (sum(passed) / sum(total)) * 100
ax.axhline(y=overall_accuracy, color='#34495e', linestyle='--', linewidth=2, 
           label=f'Overall: {overall_accuracy:.1f}%', alpha=0.7)
ax.text(len(categories) - 0.5, overall_accuracy + 3, 
        f'Overall Accuracy: {overall_accuracy:.1f}%', 
        fontsize=12, fontweight='bold', color='#34495e',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#34495e', linewidth=2))

# Add annotation for critical findings
#ax.text(0.02, 0.98, 
#        'Critical Findings:\n'
#        '✓ Perfect: Time Urgency (100%)\n'
#        '✓ Perfect: Mixed High-Risk (100%)\n'
#        '✗ Weakest: Cultural/Religious (33.3%)\n'
#        '✗ Critical Gap: Behavioral Indicators (50.0%)',
#        transform=ax.transAxes,
#        fontsize=10,
#       verticalalignment='top',
#        bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.9, edgecolor='#34495e', linewidth=2),
#        family='monospace')

plt.tight_layout()

# Save figure
output_dir = Path(__file__).parent
output_dir.mkdir(exist_ok=True)
output_path = output_dir / 'accuracy_comparison_chart.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✅ Chart saved to: {output_path}")

# Also save as high-res for presentation
output_path_highres = output_dir / 'accuracy_comparison_chart_highres.png'
plt.savefig(output_path_highres, dpi=600, bbox_inches='tight', facecolor='white')
print(f"✅ High-res chart saved to: {output_path_highres}")

plt.show()

# Print statistics summary
print("\n" + "="*60)
print("STATISTICS SUMMARY")
print("="*60)
print(f"Overall Accuracy: {overall_accuracy:.1f}% ({sum(passed)}/{sum(total)})")
print(f"\nBest Performers (100%):")
for i, (cat, acc) in enumerate(zip(categories, accuracy)):
    if acc == 100:
        print(f"  ✅ {cat.replace(chr(10), ' ')}: {passed[i]}/{total[i]}")

print(f"\nWeakest Performers (<70%):")
for i, (cat, acc) in enumerate(zip(categories, accuracy)):
    if acc < 70:
        print(f"  ❌ {cat.replace(chr(10), ' ')}: {passed[i]}/{total[i]} ({acc:.1f}%)")

print("\n" + "="*60)

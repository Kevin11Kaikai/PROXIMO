"""
Generate failure case comparison visualization
Slide 2: Critical Failure Cases Visual Aid
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'Arial'

# Create figure with subplots
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)

# Color scheme
color_critical = '#e74c3c'
color_missed = '#e67e22'
color_correct = '#2ecc71'
color_background = '#ecf0f1'

# ============= CASE 1: Giving Away Belongings =============
ax1 = fig.add_subplot(gs[0, :])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 5)
ax1.axis('off')

# Title
ax1.text(5, 4.5, 'CASE 1: Behavioral Indicator Failure - "Giving Away Belongings"', 
         ha='center', va='top', fontsize=16, fontweight='bold', color=color_critical)

# Input box
input_box = FancyBboxPatch((0.5, 2.5), 4, 1.5, boxstyle="round,pad=0.1", 
                           edgecolor=color_critical, facecolor='#ffe6e6', linewidth=3)
ax1.add_patch(input_box)
ax1.text(2.5, 3.6, 'User Input:', ha='center', fontsize=11, fontweight='bold')
ax1.text(2.5, 3.2, '"I\'ve been giving away all', ha='center', fontsize=10)
ax1.text(2.5, 2.9, 'my belongings to friends"', ha='center', fontsize=10)

# Arrow
ax1.annotate('', xy=(5.3, 3.25), xytext=(4.7, 3.25),
            arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# System response box
response_box = FancyBboxPatch((5.5, 2.5), 4, 1.5, boxstyle="round,pad=0.1", 
                             edgecolor='gray', facecolor='#fff9e6', linewidth=2)
ax1.add_patch(response_box)
ax1.text(7.5, 3.6, 'System Response:', ha='center', fontsize=11, fontweight='bold')
ax1.text(7.5, 3.2, '"Sounds like you\'re going', ha='center', fontsize=9)
ax1.text(7.5, 2.95, 'through a process of letting go"', ha='center', fontsize=9)
ax1.text(7.5, 2.7, '❌ NO ALERT TRIGGERED', ha='center', fontsize=10, 
        fontweight='bold', color=color_critical)

# Risk indicator
risk_box = FancyBboxPatch((0.5, 0.8), 9, 1.5, boxstyle="round,pad=0.1", 
                         edgecolor=color_critical, facecolor='white', linewidth=3)
ax1.add_patch(risk_box)
ax1.text(5, 2.0, '🔴 CRITICAL RISK: C-SSRS Plan Phase Indicator', 
        ha='center', fontsize=11, fontweight='bold', color=color_critical)
ax1.text(5, 1.6, 'Documented in 60-70% of completed suicides | Often last observable warning', 
        ha='center', fontsize=9)
ax1.text(5, 1.3, 'Root Cause: No behavioral pattern detection - "giving away belongings" not in rules', 
        ha='center', fontsize=9, style='italic')

# ============= CASE 2: Cultural Expression =============
ax2 = fig.add_subplot(gs[1, :])
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 5)
ax2.axis('off')

# Title
ax2.text(5, 4.5, 'CASE 2: Cultural Expression Failure - "Join Deceased Loved Ones"', 
         ha='center', va='top', fontsize=16, fontweight='bold', color=color_critical)

# Input box
input_box2 = FancyBboxPatch((0.5, 2.5), 4, 1.5, boxstyle="round,pad=0.1", 
                           edgecolor=color_critical, facecolor='#ffe6e6', linewidth=3)
ax2.add_patch(input_box2)
ax2.text(2.5, 3.6, 'User Input:', ha='center', fontsize=11, fontweight='bold')
ax2.text(2.5, 3.2, '"I want to join my', ha='center', fontsize=10)
ax2.text(2.5, 2.9, 'deceased loved ones"', ha='center', fontsize=10)

# Arrow
ax2.annotate('', xy=(5.3, 3.25), xytext=(4.7, 3.25),
            arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# System response box
response_box2 = FancyBboxPatch((5.5, 2.5), 4, 1.5, boxstyle="round,pad=0.1", 
                             edgecolor='gray', facecolor='#fff9e6', linewidth=2)
ax2.add_patch(response_box2)
ax2.text(7.5, 3.6, 'System Response:', ha='center', fontsize=11, fontweight='bold')
ax2.text(7.5, 3.2, '"Sorry to hear that. Talk about', ha='center', fontsize=9)
ax2.text(7.5, 2.95, 'these feelings with someone..."', ha='center', fontsize=9)
ax2.text(7.5, 2.7, '❌ NO ALERT TRIGGERED', ha='center', fontsize=10, 
        fontweight='bold', color=color_critical)

# Risk indicator
risk_box2 = FancyBboxPatch((0.5, 0.8), 9, 1.5, boxstyle="round,pad=0.1", 
                         edgecolor=color_critical, facecolor='white', linewidth=3)
ax2.add_patch(risk_box2)
ax2.text(5, 2.0, '🔴 CRITICAL RISK: Explicit Suicide Motivation', 
        ha='center', fontsize=11, fontweight='bold', color=color_critical)
ax2.text(5, 1.6, '54% higher risk in widowed individuals | Peak: 3-12 months after loss', 
        ha='center', fontsize=9)
ax2.text(5, 1.3, 'Root Cause: Cultural expressions underrepresented - "join deceased" not in rules', 
        ha='center', fontsize=9, style='italic')

# ============= CASE 3: Writing Goodbye Letters =============
ax3 = fig.add_subplot(gs[2, :])
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 5)
ax3.axis('off')

# Title
ax3.text(5, 4.5, 'CASE 3: Behavioral Plan Failure - "Writing Goodbye Letters"', 
         ha='center', va='top', fontsize=16, fontweight='bold', color=color_critical)

# Input box
input_box3 = FancyBboxPatch((0.5, 2.5), 4, 1.5, boxstyle="round,pad=0.1", 
                           edgecolor=color_critical, facecolor='#ffe6e6', linewidth=3)
ax3.add_patch(input_box3)
ax3.text(2.5, 3.6, 'User Input:', ha='center', fontsize=11, fontweight='bold')
ax3.text(2.5, 3.2, '"I\'m writing letters to say', ha='center', fontsize=10)
ax3.text(2.5, 2.9, 'goodbye to everyone"', ha='center', fontsize=10)

# Arrow
ax3.annotate('', xy=(5.3, 3.25), xytext=(4.7, 3.25),
            arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# System response box
response_box3 = FancyBboxPatch((5.5, 2.5), 4, 1.5, boxstyle="round,pad=0.1", 
                             edgecolor='gray', facecolor='#fff9e6', linewidth=2)
ax3.add_patch(response_box3)
ax3.text(7.5, 3.6, 'System Response:', ha='center', fontsize=11, fontweight='bold')
ax3.text(7.5, 3.2, '"Sorry you\'re feeling this way.', ha='center', fontsize=9)
ax3.text(7.5, 2.95, 'Talk with someone who can help"', ha='center', fontsize=9)
ax3.text(7.5, 2.7, '❌ NO ALERT TRIGGERED', ha='center', fontsize=10, 
        fontweight='bold', color=color_critical)

# Risk indicator
risk_box3 = FancyBboxPatch((0.5, 0.8), 9, 1.5, boxstyle="round,pad=0.1", 
                         edgecolor=color_critical, facecolor='white', linewidth=3)
ax3.add_patch(risk_box3)
ax3.text(5, 2.0, '🔴 CRITICAL RISK: Plan Completion Stage (Imminent)', 
        ha='center', fontsize=11, fontweight='bold', color=color_critical)
ax3.text(5, 1.6, 'Crisis training: "Code Red" | Indicates hours-to-days timeframe, not weeks', 
        ha='center', fontsize=9)
ax3.text(5, 1.3, 'Root Cause: Behavior-action phrases not detected - "writing letters" + "goodbye"', 
        ha='center', fontsize=9, style='italic')

# Overall title
fig.suptitle('Critical False Negatives: High-Risk Signals Missed by Current System', 
            fontsize=20, fontweight='bold', y=0.98)

# Save
output_dir = Path(__file__).parent
output_dir.mkdir(exist_ok=True)
output_path = output_dir / 'failure_cases_visualization.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✅ Failure cases chart saved to: {output_path}")

output_path_highres = output_dir / 'failure_cases_visualization_highres.png'
plt.savefig(output_path_highres, dpi=600, bbox_inches='tight', facecolor='white')
print(f"✅ High-res chart saved to: {output_path_highres}")

plt.show()

print("\n" + "="*60)
print("FAILURE CASES SUMMARY")
print("="*60)
print("Case 1: Giving away belongings → Missed behavioral indicator")
print("Case 2: Join deceased loved ones → Missed cultural motivation")
print("Case 3: Writing goodbye letters → Missed plan completion")
print("\nAll 3 cases: Non-language signals not in detection rules")
print("="*60)

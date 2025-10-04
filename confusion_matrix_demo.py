#!/usr/bin/env python3
"""
Demo script to show confusion matrix visualization for job matching evaluation
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, classification_report

def main():
    print("🔍 Confusion Matrix Demo for Job Matching Evaluation")
    print("=" * 60)

    # Example data (simulating what the test would produce)
    # True labels: Frontend Developer, Data Scientist, DevOps Engineer
    true_labels = ['Frontend Developer', 'Data Scientist', 'DevOps Engineer']
    # Predicted labels (assuming perfect classification for demo)
    predicted_labels = ['Frontend Developer', 'Data Scientist', 'DevOps Engineer']

    print("True Labels:", true_labels)
    print("Predicted Labels:", predicted_labels)
    print()

    # Map to indices
    label_map = {'Frontend Developer': 0, 'Data Scientist': 1, 'DevOps Engineer': 2}
    true_indices = [label_map[label] for label in true_labels]
    pred_indices = [label_map[label] for label in predicted_labels]

    # Compute confusion matrix
    cm = confusion_matrix(true_indices, pred_indices, labels=[0, 1, 2])
    print("Confusion Matrix (text):")
    print("Classes: [Frontend Developer, Data Scientist, DevOps Engineer]")
    print(cm)
    print()

    # Compute metrics
    precision = precision_score(true_indices, pred_indices, average='macro', zero_division=0)
    recall = recall_score(true_indices, pred_indices, average='macro', zero_division=0)
    f1 = f1_score(true_indices, pred_indices, average='macro', zero_division=0)

    print(".3f")
    print(".3f")
    print(".3f")
    print()

    # Classification report
    target_names = ['Frontend Developer', 'Data Scientist', 'DevOps Engineer']
    report = classification_report(true_indices, pred_indices, labels=[0, 1, 2],
                                 target_names=target_names, zero_division=0)
    print("Classification Report:")
    print(report)

    # Generate and save confusion matrix plot
    classes = ['Frontend Developer', 'Data Scientist', 'DevOps Engineer']
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes,
                cbar_kws={'label': 'Number of predictions'})
    plt.title('Confusion Matrix for Job Matching Classification\n(Perfect Classification Example)', fontsize=14, pad=20)
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)

    # Add text annotations
    plt.text(0.5, -0.15, f'Precision: {precision:.3f} | Recall: {recall:.3f} | F1-Score: {f1:.3f}',
             ha='center', va='center', transform=plt.gca().transAxes, fontsize=10)

    plt.tight_layout()
    plt.savefig('confusion_matrix_demo.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("✅ Confusion matrix visualization saved as 'confusion_matrix_demo.png'")
    print("\n📊 Interpretation:")
    print("- Diagonal elements show correct predictions")
    print("- Off-diagonal elements show misclassifications")
    print("- Higher values on diagonal = better performance")
    print("- The color intensity represents the magnitude of predictions")

if __name__ == "__main__":
    main()

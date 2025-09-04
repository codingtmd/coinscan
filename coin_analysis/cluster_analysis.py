import os
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from coin_analysis.factors import (
    calculate_momentum_factor,
    calculate_volatility_factor
)

def generate_cluster_analysis_report(groups: dict, binance_data: dict, output_dir: str, n_days: int):
    report_parts = ["\n## Clustering and Network Analysis\n"]

    for name, group_df in groups.items():
        if group_df.empty or len(group_df) < 3: # Need at least 3 samples for clustering
            continue
        
        report_parts.append(f"### {name.capitalize()} Group\n")

        # --- Feature Engineering ---
        feature_data = []
        for symbol in group_df['symbol']:
            if symbol in binance_data:
                daily_data = binance_data[symbol]
                feature_data.append({
                    'symbol': symbol,
                    'momentum': calculate_momentum_factor(daily_data, n_days=n_days),
                    'volatility': calculate_volatility_factor(daily_data, n_days=n_days),
                })
        
        feature_df = pd.DataFrame(feature_data).set_index('symbol').dropna()

        if len(feature_df) < 3:
            report_parts.append("Not enough data for clustering.\n")
            continue

        # --- K-Means Clustering ---
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_df)
        
        kmeans = KMeans(n_clusters=3, random_state=0, n_init=10)
        feature_df['cluster'] = kmeans.fit_predict(features_scaled)

        plt.figure(figsize=(10, 6))
        plt.scatter(feature_df['momentum'], feature_df['volatility'], c=feature_df['cluster'], cmap='viridis')
        plt.title(f'{name.capitalize()} Group - K-Means Clustering (Momentum vs. Volatility)')
        plt.xlabel('Momentum')
        plt.ylabel('Volatility')
        cluster_plot_path = os.path.join(output_dir, f'{name}_cluster_plot.png')
        plt.savefig(cluster_plot_path)
        plt.close()

        report_parts.append("#### K-Means Clustering\n")
        report_parts.append(f"![Cluster Plot]({name}_cluster_plot.png)\n\n")
        report_parts.append("Cluster Sizes:\n")
        report_parts.append(feature_df.groupby('cluster').size().to_markdown())
        report_parts.append("\n\n")

        # --- Network Analysis ---
        returns_df = pd.DataFrame({
            symbol: data['close'].pct_change()
            for symbol, data in binance_data.items() if symbol in group_df['symbol'].tolist() and not data.empty
        }).dropna()
        
        if len(returns_df.columns) < 2:
            report_parts.append("Not enough data for network analysis.\n")
            continue

        corr_matrix = returns_df.corr()
        
        G = nx.from_pandas_adjacency(corr_matrix)
        
        # Remove edges with low correlation
        threshold = 0.7
        edges_to_remove = []
        for u, v, data in G.edges(data=True):
            if abs(data['weight']) < threshold:
                edges_to_remove.append((u, v))
        G.remove_edges_from(edges_to_remove)
        
        # Remove isolated nodes
        G.remove_nodes_from(list(nx.isolates(G)))

        if not G.nodes():
            report_parts.append("No significant correlations found for network analysis.\n")
            continue

        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_size=50, font_size=8)
        plt.title(f'{name.capitalize()} Group - Correlation Network (Threshold > {threshold})')
        network_plot_path = os.path.join(output_dir, f'{name}_network_plot.png')
        plt.savefig(network_plot_path)
        plt.close()

        report_parts.append("#### Correlation Network Analysis\n")
        report_parts.append(f"![Network Plot]({name}_network_plot.png)\n\n")

        degree_centrality = nx.degree_centrality(G)
        central_nodes = sorted(degree_centrality.items(), key=lambda item: item[1], reverse=True)[:5]
        
        report_parts.append("Top 5 Most Central Nodes (by Degree Centrality):\n")
        for node, centrality in central_nodes:
            report_parts.append(f"- {node}: {centrality:.4f}\n")
        report_parts.append("\n")

    return "".join(report_parts)

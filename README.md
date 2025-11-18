# Robustez em Sistemas de Transporte Multimodal — Lisboa  
_Reprodução metodológica do artigo:_  
**Aparício, J. T., Arsénio, E., & Henriques, R. (2022). Assessing robustness in multimodal transportation systems: a case study in Lisbon.**

---

## Objetivo

Este repositório contém a **replicação metodológica completa** do estudo que avalia a **robustez estrutural da rede de transporte público multimodal da Área Metropolitana de Lisboa**, considerando ônibus, metro, trem e ferry, modelados como uma **rede multilayer (multiplex)**.
O objetivo central é analisar como **falhas (acidentais ou direcionadas)** afetam a **conectividade global** do sistema e identificar **estações críticas** para a operação da rede.

---

## Dados Utilizados

- **GTFS** de cada operador:
  - Carris Metropolitana
  - Metro de Lisboa
  - CP — Comboios de Portugal
  - Transtejo/Soflusa, etc.

Arquivos necessários por operador:

| Arquivo GTFS        | Uso                                                        |
|--------------------|------------------------------------------------------------|
| `stops.txt`        | Nós da rede (paragens/estações) com lat/lon                 |
| `routes.txt`       | Identificação do modo e linha                               |
| `trips.txt`        | Ligação rota → ida/viagem                                   |
| `stop_times.txt`   | Sequência de paragens (arestas dirigidas)                   |
| `shapes.txt`       | Geometria de trajetos (para validação espacial)             |

---

## Metodologia (Passo a Passo)

### **1. Construção das Redes Monomodais**
Para cada modo (ônibus, metro, trem, barco):

- Nós → paragens (\*stop_id*)
- Arestas → conexões sequenciais obtidas de `stop_times.txt`
- Grafo representado como **direcionado**
  
G_mode = nx.DiGraph()

### **2. Identificação de Hubs Intermodais**
- Dois nós pertencem ao mesmo hub se estiverem a menos de **100 metros**.
- Cria-se uma aresta de ligação entre modos (interlayer edge).

### **3. Construção da Rede Multilayer**

G_multi = união das redes monomodais + hubs multimodais

### **4. Cálculo de Métricas Topológicas**
- Grau de entrada/saída (`in/out-degree`)
- Centralidade de intermediação (betweenness)
- Tamanho do maior componente fortemente conectado (SCC)
- APL (Average Path Length)

### **5. Simulações de Falha (Ataques Estruturais)**

| Estratégia | Descrição |
|-----------|-----------|
| Random Removal | Remove nós aleatoriamente |
| Initial Degree (ID) | Remove nós por grau inicial |
| Initial Betweenness (IB) | Remove nós por betweenness inicial |
| Recalculate Degree (RD) | Recalcula grau após cada remoção |
| Recalculate Betweenness (RB) | Recalcula betweenness periodicamente |
| Multimodal Hubs Removal | Remove nós que conectam camadas |

Após cada remoção:
- recalcula-se o tamanho do maior SCC
- registra-se a degradação da conectividade

### **6. Métrica de Robustez (AUC Normalizado)**
Nesta etapa foi implementada a métrica utilizada no artigo original:
- A curva SCC × fração de nós removidos é integrada via AUC (Área Sob a Curva).
- O AUC é então normalizado, permitindo comparar diferentes modos e estratégias.z
- Quanto menor o AUC, menor a robustez do sistema.

**Decisões tomadas**:
- Manter o cálculo do AUC exatamente como no artigo para garantir replicação fiel.
- Normalização aplicada por modo e por estratégia.
- Correções foram feitas para garantir consistência na ordenação da fração removida e evitar curvas invertidas.


### **7. Visualização dos Resultados**
Foram geradas todas as visualizações equivalentes às do estudo:
- Distribuição de grau (em escala log-log).
- Distribuição de betweenness (em escala log-log).
- Tamanho da maior SCC × fração removida (normalizado e bruto).
- APL × fração removida.
- Número de componentes isolados × iterações.

**Ajustes realizados**:

- O script foi adaptado para ler os CSVs gerados nas etapas anteriores (metrics_summary.csv, results_all_strategies.csv).
- Correções foram necessárias devido à ausência das colunas degree e betweenness no arquivo original, exigindo reconstrução dessas métricas.
- Foram mantidos os estilos gráficos do artigo (cores, eixos, escalas e estrutura visual).
- Todos os gráficos foram salvos em /Etapa 7/figures.

### **8. Comparação Entre Modos e Estratégias**
Nesta etapa foi analisada a capacidade de cada modo de transporte resistir aos ataques estruturais.

Como o arquivo results_modes_strategies.csv já trazia os valores de AUC normalizados, o script foi ajustado para:
- Identificar automaticamente o formato do CSV.
- Usar diretamente a coluna auc_normalized, sem recalcular a curva SCC × remoção.
- Consolidar e comparar o AUC médio por modo e por estratégia.

**Resultados obtidos**:

- **Modo mais resiliente**: FERTAGUS
Apresentou o maior AUC médio, indicando perda lenta de conectividade.

- **Modo mais vulnerável**: SULFERTAGUS
Baixa redundância estrutural, conectividade cai rapidamente.

- **Estratégia mais danosa**: recalc_betweenness
Atualizar a betweenness a cada remoção maximiza a fragmentação da rede.

---

## Visualizações

As figuras geradas reproduzem as do artigo:

- Distribuição de grau
- Distribuição de betweenness
- Tamanho da maior SCC × % de nós removidos
- APL × % de nós removidos

---

## Interpretação Esperada

A rede multimodal de Lisboa apresenta **alta robustez estrutural**, mantendo conectividade global mesmo após remoções extensas.  
Contudo, **hubs intermodais** são pontos de vulnerabilidade crítica.

---

## Referência

Aparício, J. T., Arsénio, E., & Henriques, R. (2022).  
*Assessing robustness in multimodal transportation systems: a case study in Lisbon.*  
European Transport Research Review, 14(1). https://doi.org/10.1186/s12544-022-00552-3






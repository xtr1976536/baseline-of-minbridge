import os
import json
import argparse

try:
    from py2neo import Graph, Node
except ImportError:
    Graph = None
    Node = None


DEFAULT_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'knowledge_base', 'term_en_final.json')
)


class FinanceGraph:
    def __init__(self, uri: str, user: str, password: str, data_path: str = DEFAULT_DATA_PATH):
        if Graph is None or Node is None:
            raise ImportError("py2neo is required to import data into Neo4j. Install dependencies with: pip install -r requirements.txt")

        self.data_path = os.path.abspath(data_path)
        self.g = Graph(uri, auth=(user, password))

    def read_nodes(self):
        """
        读取英文金融指标JSON数据并解析为节点和关系

        返回值说明：
            terms: 术语列表，每个术语包含name_en、definition_en、别名、公式等完整信息
            concepts: 非术语的计算要素集合
            categories: 分类标签集合
            rels_calculated_by: 计算依赖关系列表
            rels_belongs_to: 分类归属关系列表
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Knowledge base file not found: {self.data_path}")

        terms = []
        concepts = set()
        categories = set()

        rels_calculated_by = []
        rels_belongs_to = []

        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_term_names = {item['term_en']['name'] for item in data}

        for item in data:
            term_name = item['term_en']['name']
            term_def = item.get('definition_en', '')

            aliases = item['term_en'].get('aliases', {})
            aliases_zh = aliases.get('chinese', [])
            aliases_en = aliases.get('english', [])
            aliases_abbr = aliases.get('abbreviations', [])

            formula_list = item.get('formula_en', [])
            code_list = item.get('code', [])
            formulas = []
            for i, formula_expr in enumerate(formula_list):
                code_impl = code_list[i] if i < len(code_list) else ''
                formulas.append({
                    'expression': formula_expr,
                    'code': code_impl
                })

            # 构建完整的术语信息
            terms.append({
                'name_en': term_name,
                'definition_en': term_def,
                'aliases_zh_en': aliases_zh,
                'aliases_en_en': aliases_en,
                'aliases_abbr_en': aliases_abbr,
                'formulas_en': formulas
            })

            # 处理计算依赖关系
            for rel in item.get('related_concepts_en', []):
                concept_name = rel['concept']
                relation_type = rel.get('relation', 'Calculation')
                if concept_name in all_term_names:
                    # 指向另一个术语
                    rels_calculated_by.append([term_name, concept_name, 'Term', relation_type])
                else:
                    # 指向一个概念（非术语）
                    concepts.add(concept_name)
                    rels_calculated_by.append([term_name, concept_name, 'Concept', relation_type])

            # 处理分类归属关系
            for cat in item.get('category_en', []):
                categories.add(cat)
                rels_belongs_to.append([term_name, cat])

        return terms, concepts, categories, rels_calculated_by, rels_belongs_to

    def create_term_nodes(self, terms):
        """
        创建 FinanceTerm_en 节点

        节点属性：
            - name_en: 术语名称（主标识）
            - definition_en: 术语定义
            - aliases_zh_en: 中文别名（JSON数组字符串）
            - aliases_en_en: 英文名称（JSON数组字符串）
            - aliases_abbr_en: 缩写（JSON数组字符串）
            - formulas_en: 计算公式（JSON数组字符串，每个元素包含expression和code）
        """
        count = 0
        for term in terms:
            # 将列表类型的属性序列化为JSON字符串存储
            node = Node(
                "FinanceTerm_en",
                name_en=term['name_en'],
                definition_en=term['definition_en'],
                aliases_zh_en=json.dumps(term['aliases_zh_en'], ensure_ascii=False),
                aliases_en_en=json.dumps(term['aliases_en_en'], ensure_ascii=False),
                aliases_abbr_en=json.dumps(term['aliases_abbr_en'], ensure_ascii=False),
                formulas_en=json.dumps(term['formulas_en'], ensure_ascii=False)
            )
            self.g.create(node)
            count += 1
            print(f"FinanceTerm_en: {count}/{len(terms)}")

    def create_node(self, label, nodes, name_property='name_en'):
        count = 0
        for node_name in nodes:
            node = Node(label, **{name_property: node_name})
            self.g.create(node)
            count += 1
            print(f"{label}: {count}/{len(nodes)}")

    def create_relationship(self, start_label, end_label, edges, rel_type, rel_name,
                            start_property='name_en', end_property='name_en'):
        """创建通用关系边"""
        unique_edges = {}
        for edge in edges:
            key = '###'.join(edge[:2])
            if key not in unique_edges:
                unique_edges[key] = edge

        count = 0
        total = len(unique_edges)
        for key, edge in unique_edges.items():
            p, q = edge[0], edge[1]
            query = (
                f"MATCH (p:{start_label}), (q:{end_label}) "
                f"WHERE p.{start_property} = $start_name AND q.{end_property} = $end_name "
                f"CREATE (p)-[rel:{rel_type} {{name: $rel_name}}]->(q)"
            )
            try:
                self.g.run(query, start_name=p, end_name=q, rel_name=rel_name)
                count += 1
                print(f"{rel_type}: {count}/{total}")
            except Exception as e:
                print(f"Error: {e}")

    def create_calculated_by_relationship(self, rels_calculated_by):
        """
        创建 CALCULATED_BY 计算依赖关系
        """
        count = 0
        total = len(rels_calculated_by)
        for edge in rels_calculated_by:
            term_name, target_name, target_type, relation_type = edge
            end_label = "FinanceTerm_en" if target_type == "Term" else "FinanceConcept_en"
            query = (
                f"MATCH (p:FinanceTerm_en), (q:{end_label}) "
                f"WHERE p.name_en = $term_name AND q.name_en = $target_name "
                "CREATE (p)-[rel:CALCULATED_BY_EN {name: $rel_name, type: $relation_type}]->(q)"
            )
            try:
                self.g.run(
                    query,
                    term_name=term_name,
                    target_name=target_name,
                    rel_name='Calculation Dependency',
                    relation_type=relation_type
                )
                count += 1
                print(f"CALCULATED_BY_EN: {count}/{total}")
            except Exception as e:
                print(f"Error: {e}")

    def create_indexes(self):
        """
        创建索引加速查询
        """
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:FinanceTerm_en) ON (n.name_en)",
            "CREATE INDEX IF NOT EXISTS FOR (n:FinanceConcept_en) ON (n.name_en)",
            "CREATE INDEX IF NOT EXISTS FOR (n:FinanceCategory_en) ON (n.name_en)"
        ]
        for idx in indexes:
            try:
                self.g.run(idx)
                print(f"Index created: {idx}")
            except Exception as e:
                print(f"Index error: {e}")

    def create_graphnodes(self):
        """创建所有节点"""
        terms, concepts, categories, _, _ = self.read_nodes()

        self.create_term_nodes(terms)
        self.create_node('FinanceConcept_en', concepts)
        self.create_node('FinanceCategory_en', categories)

        # 打印统计信息
        print("=" * 50)
        print("节点统计：")
        print(f"  FinanceTerm_en（术语）: {len(terms)}")
        print(f"  FinanceConcept_en（概念）: {len(concepts)}")
        print(f"  FinanceCategory_en（分类）: {len(categories)}")
        print(f"  总计: {len(terms) + len(concepts) + len(categories)}")
        print("=" * 50)

    def create_graphrels(self):
        """创建所有关系边"""
        terms, concepts, categories, rels_calculated_by, rels_belongs_to = self.read_nodes()

        self.create_calculated_by_relationship(rels_calculated_by)
        self.create_relationship(
            'FinanceTerm_en',
            'FinanceCategory_en',
            rels_belongs_to,
            'BELONGS_TO_EN',
            'Belongs To Category'
        )

        # 打印统计信息
        print("=" * 50)
        print("关系统计：")
        print(f"  CALCULATED_BY_EN（计算依赖）: {len(rels_calculated_by)}")
        print(f"  BELONGS_TO_EN（分类归属）: {len(rels_belongs_to)}")
        print(f"  总计: {len(rels_calculated_by) + len(rels_belongs_to)}")
        print("=" * 50)

    def clear_existing_graph(self):
        """删除本脚本创建的英文知识图谱节点和关系。"""
        query = """
        MATCH (n)
        WHERE n:FinanceTerm_en OR n:FinanceConcept_en OR n:FinanceCategory_en
        DETACH DELETE n
        """
        self.g.run(query)
        print("Existing English finance graph data cleared.")

    def build(self):
        """构建完整的知识图谱"""
        print("=" * 50)
        print("开始构建金融知识图谱")
        print(f"数据文件: {self.data_path}")
        print("=" * 50)

        print("\n[1/3] 创建索引...")
        self.create_indexes()

        print("\n[2/3] 创建节点...")
        self.create_graphnodes()

        print("\n[3/3] 创建关系...")
        self.create_graphrels()

        print("\n" + "=" * 50)
        print("金融知识图谱构建完成！")
        print("=" * 50)


def parse_args():
    parser = argparse.ArgumentParser(description="Import the financial metric knowledge base into Neo4j.")
    parser.add_argument(
        "--uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j Bolt URI. Can also be set with NEO4J_URI."
    )
    parser.add_argument(
        "--user",
        default=os.getenv("NEO4J_USER", "neo4j"),
        help="Neo4j username. Can also be set with NEO4J_USER."
    )
    parser.add_argument(
        "--password",
        default=os.getenv("NEO4J_PASSWORD", ""),
        help="Neo4j password. Can also be set with NEO4J_PASSWORD."
    )
    parser.add_argument(
        "--data-path",
        default=DEFAULT_DATA_PATH,
        help="Path to the knowledge base JSON file."
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing FinanceTerm_en/FinanceConcept_en/FinanceCategory_en data before import."
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    handler = FinanceGraph(
        uri=args.uri,
        user=args.user,
        password=args.password,
        data_path=args.data_path
    )
    if args.clear:
        handler.clear_existing_graph()
    handler.build()

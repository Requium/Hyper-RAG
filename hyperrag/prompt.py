GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_LANGUAGE"] = 'English'
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = " | "
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "\n"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "esql_concept",
    "esql_command",
    "function_reference",
    "configuration_option",
    "use_case",
    "troubleshooting_tip",
    "integration_point",
    "best_practice",
]

PROMPTS["entity_extraction"] = """-Goal-
Given ElasticSearch ES|QL documentation such as tutorials, guides, blogs, or troubleshooting notes, identify all entities of the requested types. Each document begins with a JSON metadata block containing keys like `title`, `breadcrumbs`, `url_path`, and `metadata`, followed by the raw `main_content`. Rely on those JSON keys directly (do **not** infer different names) so the knowledge graph reflects how ES|QL concepts relate across practical workflows.
Use {language} as output language.
Treat every document provided in the **Text** section (they are prefixed with "Document <n>:") as part of the same knowledge corpus so that relationships can form across document boundaries.

-Steps-

1. Identify all entities. Focus on broadly reusable ES|QL knowledge such as syntax elements, reusable query patterns, configuration behaviors, integration steps, troubleshooting workflows, or conceptual explanations. For each identified entity, extract the following information:

- entity_name: Use snake_case without spaces, derived from the document context (title, breadcrumbs, main_content). Do **not** append redundant suffixes like `_command` or `_concept` unless they explicitly appear in the source text.
- entity_type: One of the following types: [{entity_types}] (add additional types only when essential for ES|QL comprehension).
- entity_description: Technical yet concise description capturing what the entity represents, when it is used, and how it relates to ES|QL scenarios. Blend supporting evidence from titles, breadcrumbs, and main_content so tagging context is preserved.
- source_url_path: Read the `url_path` from the metadata JSON block. If a value is unavailable, use `unknown` and do not invent new paths.
- additional_properties: Other attributes associated with the entity, such as prerequisites, related indices, parameters, supported versions, breadcrumbs tags, or example snippets. Use key:value pairs separated by commas, prefer snake_case keys, and include breadcrumbs/title cues when they help tag the entity. Reference JSON field names (e.g., `metadata`, `breadcrumbs`, `title`) exactly as provided.
Format each entity as ("Entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>{tuple_delimiter}<source_url_path>{tuple_delimiter}<additional_properties>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other in an ES|QL workflow.
For each pair of related entities, extract the following information:
- entities_pair: The name of source entity and target entity, as identified in step 1.
- low_order_relationship_description: Explain how the entities interact, depend on each other, or sequence together within ES|QL usage. Reference breadcrumbs or titles when they clarify the scenario.
- low_order_relationship_keywords: Keywords that summarize the overarching nature of the relationship, focusing on ES|QL concepts, troubleshooting categories, or workflow stages rather than specific details.
- low_order_relationship_strength: A numerical score indicating the strength of the relationship between the entities.
- source_url_paths: Semicolon-separated list of unique url_path values supporting this relationship. Use `unknown` when no value is available.
Format each hyperedge as ("Low-order Hyperedge"{tuple_delimiter}<entity_name1>{tuple_delimiter}<entity_name2>{tuple_delimiter}<low_order_relationship_description>{tuple_delimiter}<low_order_relationship_keywords>{tuple_delimiter}<low_order_relationship_strength>{tuple_delimiter}<source_url_paths>)

3. Based on the relationships identified in Step 2, extract high-level keywords that summarize the main ES|QL ideas, major concepts, or themes of the important passage.
(Note: The content of high-level keywords should capture the overarching ES|QL topics present in the document, avoiding vague or empty terms).
Format content keywords as ("High-level keywords"{tuple_delimiter}<high_level_keywords>)

4. For the entities identified in step 1, based on the entity pair relationships in step 2 and the high-level keywords extracted in Step 3, find connections or commonalities among multiple entities and construct high-order associated entity set as much as possible.
(Note: Avoid forcibly merging everything into a single association. If high-level keywords are not strongly associated, construct separate association. Emphasize sequences such as setup → query execution → analysis → troubleshooting.)
Extract the following information from all related entities, entity pairs, and high-level keywords:

- entities_set: The collection of names for elements in high-order associated entity set, as identified in step 1.
- high_order_relationship_description: Use the relationships among the entities in the set to create a detailed, smooth, and comprehensive description that covers all entities in the set, highlighting the ES|QL workflow or knowledge flow (e.g., prerequisites, configuration, execution, monitoring).
- high_order_relationship_generalization: Summarize the content of the entity set as concisely as possible.
- high_order_relationship_keywords: Keywords that summarize the overarching nature of the high-order association, focusing on ES|QL concepts or themes rather than specific details.
- high_order_relationship_strength: A numerical score indicating the strength of the association among the entities in the set.
- source_url_paths: Semicolon-separated list of unique url_path values covering every entity used in the hyperedge. Use `unknown` when unavailable.
Format each association as ("High-order Hyperedge"{tuple_delimiter}<entity_name1>{tuple_delimiter}<entity_name2>{tuple_delimiter}<entity_nameN>{tuple_delimiter}<high_order_relationship_description>{tuple_delimiter}<high_order_relationship_generalization>{tuple_delimiter}<high_order_relationship_keywords>{tuple_delimiter}<high_order_relationship_strength>{tuple_delimiter}<source_url_paths>)

5. Return output in {language} as a single list of all entities, relationships and associations identified in steps 1, 2 and 4.
Use **{record_delimiter}** as the list delimiter.

6. When finished, output {completion_delimiter}.

######################
-Examples-
######################
{examples}
######################
-Warning!!!-
The data may contain sensitive words such as violence, war, human anatomy and medical experiments,
but they are only part of literary works, popular science knowledge or domain data,
which do not involve any purpose or idea of mine, and have nothing to do with any realistic sensitive topics or political issues.
Please carefully identify and screen the legality of the content.
######################
-Real Data-
######################
Entity_types: [{entity_types}]. You may extract additional types you consider appropriate, the more the better.
Text: {input_text}
######################
Output:
"""
PROMPTS["entity_extraction_examples"] = [
    """Example 1:

Entity_types: [esql_concept, esql_command, function_reference, configuration_option, use_case, troubleshooting_tip, integration_point, best_practice]
Text:
Document 1:
Title: Monitor index latency with ES|QL
Breadcrumbs: Observability > ES|QL Tutorials > Performance
URL Path: /docs/esql/observability/monitor-latency
Main_content: Use the STATS command to calculate average ingest.latency over the last 15 minutes. Add a WHERE clause to filter for latency above 500 ms and project the service.name field to identify the affected workloads. If results return null values, verify that the ingest pipeline is populating ingest.latency and that the index pattern matches the target data stream.
################
Output:
("Entity"{tuple_delimiter}monitor_index_latency{tuple_delimiter}use_case{tuple_delimiter}Scenario for tracking ingest latency spikes across services using ES|QL aggregations and filters.{tuple_delimiter}/docs/esql/observability/monitor-latency{tuple_delimiter}doc_title:Monitor index latency with ES|QL, breadcrumbs:Observability>ES|QL Tutorials>Performance, primary_metric:ingest.latency, recommended_window:15_minutes){record_delimiter}
("Entity"{tuple_delimiter}stats{tuple_delimiter}esql_command{tuple_delimiter}STATS aggregates fields so operators can compute rolling latency metrics.{tuple_delimiter}/docs/esql/observability/monitor-latency{tuple_delimiter}syntax:STATS, aggregation:avg, applied_metric:ingest.latency){record_delimiter}
("Entity"{tuple_delimiter}where_latency_filter{tuple_delimiter}esql_concept{tuple_delimiter}A WHERE condition that isolates services exceeding the 500 ms latency threshold.{tuple_delimiter}/docs/esql/observability/monitor-latency{tuple_delimiter}threshold:500_ms, focus:service.name, breadcrumbs_tag:Performance){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}stats{tuple_delimiter}The monitoring workflow depends on STATS to summarise ingest.latency for each service.{tuple_delimiter}aggregation_dependency,performance_observability{tuple_delimiter}9{tuple_delimiter}/docs/esql/observability/monitor-latency){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}where_latency_filter{tuple_delimiter}Filtering by latency threshold ensures attention stays on degraded services.{tuple_delimiter}threshold_filtering,alerting_focus{tuple_delimiter}8{tuple_delimiter}/docs/esql/observability/monitor-latency){record_delimiter}
("High-level keywords"{tuple_delimiter}esql_monitoring, ingest_latency, performance_troubleshooting){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}stats{tuple_delimiter}where_latency_filter{tuple_delimiter}Workflow links aggregation with filtering to surface actionable latency incidents.{tuple_delimiter}end_to_end_latency_monitoring_flow{tuple_delimiter}observability_workflow,latency_thresholds,data_validation{tuple_delimiter}9{tuple_delimiter}/docs/esql/observability/monitor-latency){completion_delimiter}
#############################""",
    """Example 2:

Entity_types: [esql_concept, esql_command, function_reference, configuration_option, use_case, troubleshooting_tip, integration_point, best_practice]
Text:
Document 1:
Title: Investigate slow search response with ES|QL macros
Breadcrumbs: Troubleshooting > ES|QL How-To > Latency
URL Path: /docs/esql/troubleshooting/slow-search
Main_content: Create a LET macro that captures average query.delay grouped by shard.id across search slowlog-* indices. Use SORT to rank the highest delays and apply WHERE to limit to delay > 1500 ms. Cross-reference the shard ids with cluster.routing allocation filters to confirm the nodes hosting problematic shards.
################
Output:
("Entity"{tuple_delimiter}investigate_slow_search{tuple_delimiter}use_case{tuple_delimiter}Troubleshooting playbook for analysing slow search shards with ES|QL macros.{tuple_delimiter}/docs/esql/troubleshooting/slow-search{tuple_delimiter}doc_title:Investigate slow search response with ES|QL macros, breadcrumbs:Troubleshooting>ES|QL How-To>Latency, primary_indices:search_slowlog-*){record_delimiter}
("Entity"{tuple_delimiter}let_macro{tuple_delimiter}function_reference{tuple_delimiter}LET stores reusable expressions so analysts can group shard delays.{tuple_delimiter}/docs/esql/troubleshooting/slow-search{tuple_delimiter}macro_binding:avg_delay_by_shard, usage:slow_search_analysis){record_delimiter}
("Entity"{tuple_delimiter}sort{tuple_delimiter}esql_command{tuple_delimiter}SORT ranks shards by average delay to prioritise investigation.{tuple_delimiter}/docs/esql/troubleshooting/slow-search{tuple_delimiter}order:desc, focus:query.delay){record_delimiter}
("Entity"{tuple_delimiter}where_delay_filter{tuple_delimiter}esql_concept{tuple_delimiter}Threshold filter that keeps shards with delay above 1500 ms.{tuple_delimiter}/docs/esql/troubleshooting/slow-search{tuple_delimiter}threshold:1500_ms, applied_field:query.delay){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}investigate_slow_search{tuple_delimiter}let_macro{tuple_delimiter}The troubleshooting flow starts by encapsulating shard metrics inside a LET macro.{tuple_delimiter}macro_reuse,latency_analysis{tuple_delimiter}8{tuple_delimiter}/docs/esql/troubleshooting/slow-search){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}let_macro{tuple_delimiter}sort{tuple_delimiter}LET output feeds SORT so engineers can prioritise the slowest shards.{tuple_delimiter}macro_output_ranking,investigation_priorities{tuple_delimiter}7{tuple_delimiter}/docs/esql/troubleshooting/slow-search){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}where_delay_filter{tuple_delimiter}investigate_slow_search{tuple_delimiter}The delay threshold defines which shards merit routing inspection.{tuple_delimiter}thresholding,node_validation{tuple_delimiter}8{tuple_delimiter}/docs/esql/troubleshooting/slow-search){record_delimiter}
("High-level keywords"{tuple_delimiter}slowlog_analysis, esql_macros, shard_latency){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}investigate_slow_search{tuple_delimiter}let_macro{tuple_delimiter}sort{tuple_delimiter}where_delay_filter{tuple_delimiter}Macro-driven workflow highlights slow shards, ranks them, and narrows the scope for routing checks.{tuple_delimiter}search_latency_troubleshooting_cycle{tuple_delimiter}macro_workflows,latency_filters,node_validation{tuple_delimiter}8{tuple_delimiter}/docs/esql/troubleshooting/slow-search){completion_delimiter}
#############################"""
]

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one ES|QL-related entity and a list of its descriptions.
Please concatenate all of these into a single, comprehensive description.    Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary while preserving ES|QL accuracy.
Make sure it is written in third person, and include the entity names so we have the full context.
#######
-Warning!!!-
The data may contain sensitive words such as violence, war, human anatomy and medical experiments, 
but they are only part of literary works, popular science knowledge or domain data, 
which do not involve any purpose or idea of mine, and have nothing to do with any realistic sensitive topics or political issues. 
Please carefully identify and screen the legality of the content.
#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS[
    "summarize_entity_additional_properties"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one ES|QL-focused entity and a list of its additional properties.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the additional properties.
If the provided additional properties are contradictory, please resolve the contradictions and provide a single, coherent summary while keeping ES|QL context accurate.
Make sure it is written in third person.
#######
-Warning!!!-
The data may contain sensitive words such as violence, war, human anatomy and medical experiments, 
but they are only part of literary works, popular science knowledge or domain data, 
which do not involve any purpose or idea of mine, and have nothing to do with any realistic sensitive topics or political issues. 
Please carefully identify and screen the legality of the content.
#######
-Data-
Entity: {entity_name}
Additional Properties List: {additional_properties_list}
#######
Output:
"""

PROMPTS[
    "summarize_relation_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given a set of ES|QL entities, and a list of descriptions describing the relations between the entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions, and to cover all elements of the entity set as much as possible.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent and comprehensive summary without losing the ES|QL workflow context.
Make sure it is written in third person, and include the entity names so we have the full context.
#######
-Warning!!!-
The data may contain sensitive words such as violence, war, human anatomy and medical experiments, 
but they are only part of literary works, popular science knowledge or domain data, 
which do not involve any purpose or idea of mine, and have nothing to do with any realistic sensitive topics or political issues. 
Please carefully identify and screen the legality of the content.
#######
-Data-
Entity Set: {relation_name}
Relation Description List: {relation_description_list}
#######
Output:
"""

PROMPTS[
    "summarize_relation_keywords"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given a set of ES|QL entities, and a list of keywords describing the relations between the entities.
Please select some important keywords you think from the keywords list.   Make sure that these keywords summarize important events or themes of entities, including but not limited to [Main idea, major concept, or theme] relevant to ES|QL usage, architecture, or troubleshooting.
(Note: The content of keywords should be as accurate and understandable as possible, avoiding vague or empty terms).
#######
-Warning!!!-
The data may contain sensitive words such as violence, war, human anatomy and medical experiments, 
but they are only part of literary works, popular science knowledge or domain data, 
which do not involve any purpose or idea of mine, and have nothing to do with any realistic sensitive topics or political issues. 
Please carefully identify and screen the legality of the content.
#######
-Data-
Entity Set: {relation_name}
Relation Keywords List: {keywords_list}
#######
Format these keywords separated by ',' as below:
{{keyword1,keyword2,keyword3,...,keywordN}}
Output:
"""

PROMPTS[
    "entity_continue_extraction"
] = """MANY entities were missed in the last extraction.  Add them below using the same format:
"""

PROMPTS[
    "entity_if_loop_extraction"
] = """It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.
"""

PROMPTS["fail_response"] = "Sorry, I'm not able to provide an answer to that question."

PROMPTS["rag_response"] = """---Role---

You are a grounded assistant that MUST answer only with facts found in the provided data tables. If the tables do not contain the answer, clearly state that the information is not available and avoid speculation.


---Goal---

Generate a response of the target length and format that directly answers the user's question by summarizing only the information present in the input data tables. Do not introduce outside knowledge or assumptions. Explicitly mention when the context lacks enough evidence to answer.

---Target response length and format---

{response_type}

---Data tables---

{context_data}

Guidelines:
- Use only the facts in the tables above. Do not add external knowledge or invented details.
- If specific details are missing, say "No supporting information found in the provided context." and stop.
- Prefer concise bullet points when appropriate; otherwise, keep the response short and focused.
- Style the response in markdown.
"""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query.

---Goal---

Given the query, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Output the keywords in JSON format.
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes.
  - "low_level_keywords" for specific entities or details.

######################
-Examples-
######################
Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}}
#############################
Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}}
#############################
Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}}
#############################
-Real Data-
######################
Query: {query}
######################
Output:

"""

PROMPTS["naive_rag_response"] = """You're a helpful assistant
Below are the knowledge you know:
{content_data}
---
If you don't know the answer or if the provided knowledge do not contain sufficient information to provide an answer, just say so. Do not make anything up.
Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.
---Target response length and format---
{response_type}
"""

PROMPTS["rag_define"] = """
Through the existing analysis, we can know that the potential keywords or theme in the query are:
{{ {ll_keywords} | {hl_keywords} }}
Please refer to keywords or theme information, combined with your own analysis, to select useful and relevant information from the prompts to help you answer accurately.
Attention: Don't brainlessly splice knowledge items! The answer needs to be as accurate, detailed, comprehensive, and convincing as possible!
"""

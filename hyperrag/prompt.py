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
Given ElasticSearch ES|QL documentation such as tutorials, guides, blogs, or troubleshooting notes that include fields like titles, breadcrumbs, and main_content, identify all entities of the requested types. Then construct hyperedges by extracting complex relationships among the identified entities so the knowledge graph reflects how ES|QL concepts relate across practical workflows.
Use {language} as output language.

-Steps-

1. Identify all entities. Focus on broadly reusable ES|QL knowledge such as syntax elements, reusable query patterns, configuration behaviors, integration steps, troubleshooting workflows, or conceptual explanations. For each identified entity, extract the following information:

- entity_name: Use snake_case without spaces, derived from the document context (title, breadcrumbs, main_content).
- entity_type: One of the following types: [{entity_types}] (add additional types only when essential for ES|QL comprehension).
- entity_description: Technical yet concise description capturing what the entity represents, when it is used, and how it relates to ES|QL scenarios from tutorials, guides, blogs, or troubleshooting content.
- additional_properties: Other attributes associated with the entity, such as prerequisites, related indices, parameters, supported versions, common pitfalls, or example snippets. Use key:value pairs separated by commas and prefer snake_case keys.
Format each entity as ("Entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>{tuple_delimiter}<additional_properties>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other in an ES|QL workflow.
For each pair of related entities, extract the following information:
- entities_pair: The name of source entity and target entity, as identified in step 1.
- low_order_relationship_description: Explain how the entities interact, depend on each other, or sequence together within ES|QL usage. Reference breadcrumbs or titles when they clarify the scenario.
- low_order_relationship_keywords: Keywords that summarize the overarching nature of the relationship, focusing on ES|QL concepts, troubleshooting categories, or workflow stages rather than specific details.
- low_order_relationship_strength: A numerical score indicating the strength of the relationship between the entities.
Format each hyperedge as ("Low-order Hyperedge"{tuple_delimiter}<entity_name1>{tuple_delimiter}<entity_name2>{tuple_delimiter}<low_order_relationship_description>{tuple_delimiter}<low_order_relationship_keywords>{tuple_delimiter}<low_order_relationship_strength>)

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
Format each association as ("High-order Hyperedge"{tuple_delimiter}<entity_name1>{tuple_delimiter}<entity_name2>{tuple_delimiter}<entity_nameN>{tuple_delimiter}<high_order_relationship_description>{tuple_delimiter}<high_order_relationship_generalization>{tuple_delimiter}<high_order_relationship_keywords>{tuple_delimiter}<high_order_relationship_strength>)

5. Return output in {language} as a single list of all entities, relationships and associations identified in steps 1, 2 and 4. Use **{record_delimiter}** as the list delimiter.

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
Title: Monitor index latency with ES|QL
Breadcrumbs: Observability > ES|QL Tutorials > Performance
Main_content: Use the STATS command to calculate average ingest.latency over the last 15 minutes. Add a WHERE clause to filter for latency above 500 ms and project the service.name field to identify the affected workloads. If results return null values, verify that the ingest pipeline is populating ingest.latency and that the index pattern matches the target data stream.
################
Output:
("Entity"{tuple_delimiter}monitor_index_latency{tuple_delimiter}use_case{tuple_delimiter}This use case explains how ES|QL helps operations teams monitor ingest latency across services by calculating rolling averages and filtering slow pipelines.{tuple_delimiter}doc_title:Monitor index latency with ES|QL, primary_metric:ingest.latency, recommended_window:15_minutes){record_delimiter}
("Entity"{tuple_delimiter}stats_command{tuple_delimiter}esql_command{tuple_delimiter}STATS aggregates event fields in ES|QL queries, enabling metrics like average ingest.latency to be computed across time windows.{tuple_delimiter}syntax:STATS, aggregation:avg, supported_targets:data_streams){record_delimiter}
("Entity"{tuple_delimiter}where_latency_filter{tuple_delimiter}function_reference{tuple_delimiter}The WHERE clause filters events with ingest.latency greater than 500 ms so the query highlights only problematic services.{tuple_delimiter}comparison_operator:>, threshold:500_ms, recommended_field:ingest.latency){record_delimiter}
("Entity"{tuple_delimiter}ingest_pipeline_validation{tuple_delimiter}troubleshooting_tip{tuple_delimiter}If STATS returns null metrics, validate that the ingest pipeline populates ingest.latency and that the index pattern targets the correct data stream.{tuple_delimiter}breadcrumbs:Observability>ES|QL Tutorials>Performance, remediation:confirm_pipeline_fields, check:index_pattern_alignment){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}stats_command{tuple_delimiter}The latency monitoring scenario depends on STATS to aggregate ingest.latency values for each service.{tuple_delimiter}aggregation_dependency,performance_observability{tuple_delimiter}9){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}where_latency_filter{tuple_delimiter}The WHERE clause enforces the latency threshold that focuses the monitoring workflow on high-latency services.{tuple_delimiter}threshold_filtering,alerting_focus{tuple_delimiter}8){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}ingest_pipeline_validation{tuple_delimiter}Troubleshooting guidance ensures the monitoring workflow remains accurate when query results contain null values.{tuple_delimiter}data_quality_check,workflow_resilience{tuple_delimiter}7){record_delimiter}
("High-level keywords"{tuple_delimiter}esql_monitoring, ingest_latency, performance_troubleshooting){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}monitor_index_latency{tuple_delimiter}stats_command{tuple_delimiter}where_latency_filter{tuple_delimiter}ingest_pipeline_validation{tuple_delimiter}Together these entities describe the full ES|QL workflow for identifying slow ingest pipelines: aggregate latency metrics, focus on problematic services, and validate pipeline data when anomalies appear.{tuple_delimiter}end_to_end_latency_monitoring_flow{tuple_delimiter}observability_workflow,latency_thresholds,data_validation{tuple_delimiter}9){completion_delimiter}
#############################""",
    """Example 2:

Entity_types: [esql_concept, esql_command, function_reference, configuration_option, use_case, troubleshooting_tip, integration_point, best_practice]
Text:
Title: Correlate endpoint alerts with ES|QL JOIN
Breadcrumbs: Security Analytics > ES|QL Guides > Correlation
Main_content: Use the JOIN command to combine endpoint.alerts with cloud.audit entries on the user.name field. Project action.name, agent.id, and kibana.alert.rule.name to highlight rule matches that triggered both data sources. If JOIN returns empty rows, confirm that timestamp fields are aligned and that enrich policies are populating the audit index with host.name references.
################
Output:
("Entity"{tuple_delimiter}correlate_endpoint_alerts{tuple_delimiter}use_case{tuple_delimiter}This use case outlines how security analysts join endpoint alerts with cloud audit events to confirm cross-data-source detections using ES|QL.{tuple_delimiter}doc_title:Correlate endpoint alerts with ES|QL JOIN, primary_indices:endpoint.alerts|cloud.audit, correlation_focus:user.name){record_delimiter}
("Entity"{tuple_delimiter}join_command{tuple_delimiter}esql_command{tuple_delimiter}JOIN merges documents from two indices on a shared key, enabling side-by-side inspection of related security events.{tuple_delimiter}required_fields:user.name, recommended_projection:action.name|agent.id){record_delimiter}
("Entity"{tuple_delimiter}enrich_security_lookup{tuple_delimiter}integration_point{tuple_delimiter}Enrich policies supply host.name context to audit events so JOIN outputs include machine attribution.{tuple_delimiter}enrich_policy:audit-host, dependency:ingest_pipeline){record_delimiter}
("Entity"{tuple_delimiter}alert_response_playbook{tuple_delimiter}best_practice{tuple_delimiter}Guidance for analysts to verify joined alerts, escalate correlated findings, and update detection rules when mismatches occur.{tuple_delimiter}recommended_steps:validate_timestamps|notify_incident_response){record_delimiter}
("Entity"{tuple_delimiter}join_empty_result_diagnosis{tuple_delimiter}troubleshooting_tip{tuple_delimiter}Checklist for resolving empty JOIN results caused by misaligned timestamps or missing enrich metadata.{tuple_delimiter}validation_actions:compare_event_time|reindex_enrich_source){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}correlate_endpoint_alerts{tuple_delimiter}join_command{tuple_delimiter}The use case depends on JOIN to overlay endpoint alerts with audit events for correlation.{tuple_delimiter}cross_index_analysis,detection_validation{tuple_delimiter}9){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}join_command{tuple_delimiter}enrich_security_lookup{tuple_delimiter}JOIN requires enriched host.name data to contextualize results across indices.{tuple_delimiter}context_enrichment,host_attribution{tuple_delimiter}8){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}join_command{tuple_delimiter}join_empty_result_diagnosis{tuple_delimiter}Troubleshooting guidance addresses failures encountered when executing JOIN across asynchronous event streams.{tuple_delimiter}query_debugging,timestamp_alignment{tuple_delimiter}7){record_delimiter}
("High-level keywords"{tuple_delimiter}esql_join, security_correlation, enrich_policies, incident_validation){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}correlate_endpoint_alerts{tuple_delimiter}join_command{tuple_delimiter}enrich_security_lookup{tuple_delimiter}alert_response_playbook{tuple_delimiter}join_empty_result_diagnosis{tuple_delimiter}These entities define the full correlation workflow: prepare enriched indices, execute JOIN, review aligned detections, and troubleshoot gaps before escalating incident response.{tuple_delimiter}end_to_end_security_correlation{tuple_delimiter}cross_index_joining,alert_validation,response_readiness{tuple_delimiter}9){completion_delimiter}
#############################""",
    """Example 3:

Entity_types: [esql_concept, esql_command, function_reference, configuration_option, use_case, troubleshooting_tip, integration_point, best_practice]
Text:
Title: Optimize ES|QL dashboards for weekly reporting
Breadcrumbs: Operations > ES|QL Blogs > Performance
Main_content: Schedule ES|QL queries with the PERSIST keyword to materialize weekly aggregates for dashboard widgets. Combine STATS with EVAL to derive uptime.percent and latency.p95. Configure data view caching so dashboards refresh quickly even when querying large metricbeat-* indices.
################
Output:
("Entity"{tuple_delimiter}optimize_esql_dashboards{tuple_delimiter}use_case{tuple_delimiter}A workflow describing how operations teams pre-compute ES|QL metrics to keep weekly dashboards responsive.{tuple_delimiter}doc_title:Optimize ES|QL dashboards for weekly reporting, audience:operations_engineers){record_delimiter}
("Entity"{tuple_delimiter}stats_command{tuple_delimiter}esql_command{tuple_delimiter}STATS aggregates numeric fields like uptime and latency to build summary metrics for visualization.{tuple_delimiter}recommended_fields:uptime.percent|latency.p95){record_delimiter}
("Entity"{tuple_delimiter}eval_keyword{tuple_delimiter}function_reference{tuple_delimiter}EVAL derives calculated metrics, such as uptime.percent, to support business-level reporting.{tuple_delimiter}calculation_examples:uptime.percent|latency.p95){record_delimiter}
("Entity"{tuple_delimiter}persist_keyword{tuple_delimiter}configuration_option{tuple_delimiter}PERSIST stores ES|QL results so dashboards can reuse cached aggregates without recomputing heavy queries.{tuple_delimiter}scheduling:weekly, storage:index_snapshots){record_delimiter}
("Entity"{tuple_delimiter}data_view_caching{tuple_delimiter}integration_point{tuple_delimiter}Dashboards rely on data view caching to accelerate loading of persisted ES|QL results.{tuple_delimiter}cache_scope:metricbeat-*, refresh_interval:15_minutes){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}optimize_esql_dashboards{tuple_delimiter}persist_keyword{tuple_delimiter}The use case centers on persisting query outputs to reduce dashboard latency.{tuple_delimiter}result_materialization,reporting_efficiency{tuple_delimiter}9){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}stats_command{tuple_delimiter}eval_keyword{tuple_delimiter}STATS metrics feed EVAL-derived calculations that make uptime and latency insights actionable.{tuple_delimiter}metric_engineering,derived_fields{tuple_delimiter}8){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}persist_keyword{tuple_delimiter}data_view_caching{tuple_delimiter}Persisted tables benefit from dashboard caching to serve users quickly.{tuple_delimiter}performance_tuning,cached_views{tuple_delimiter}7){record_delimiter}
("High-level keywords"{tuple_delimiter}dashboard_performance, esql_stats, persisted_results, caching_strategy){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}optimize_esql_dashboards{tuple_delimiter}stats_command{tuple_delimiter}eval_keyword{tuple_delimiter}persist_keyword{tuple_delimiter}data_view_caching{tuple_delimiter}Together these entities describe the performance loop: aggregate metrics, derive new values, persist outputs, and accelerate dashboards with caching.{tuple_delimiter}weekly_reporting_pipeline{tuple_delimiter}metrics_aggregation,derived_insights,performance_tuning{tuple_delimiter}8){completion_delimiter}
#############################""",
    """Example 4:

Entity_types: [esql_concept, esql_command, function_reference, configuration_option, use_case, troubleshooting_tip, integration_point, best_practice]
Text:
Title: Investigate slow search response with ES|QL macros
Breadcrumbs: Troubleshooting > ES|QL How-To > Latency
Main_content: Create a LET macro that captures average query.delay grouped by shard.id across search slowlog-* indices. Use SORT to rank the highest delays and apply WHERE to limit to delay > 1500 ms. Cross-reference the shard ids with cluster.routing allocation filters to confirm the nodes hosting problematic shards.
################
Output:
("Entity"{tuple_delimiter}investigate_slow_search{tuple_delimiter}use_case{tuple_delimiter}A troubleshooting scenario documenting how engineers analyze ES|QL slowlog data to pinpoint overloaded shards.{tuple_delimiter}doc_title:Investigate slow search response with ES|QL macros, primary_indices:search_slowlog-*){record_delimiter}
("Entity"{tuple_delimiter}let_macro{tuple_delimiter}function_reference{tuple_delimiter}LET stores reusable ES|QL expressions that capture average query delay per shard.{tuple_delimiter}macro_binding:avg_delay_by_shard){record_delimiter}
("Entity"{tuple_delimiter}sort_command{tuple_delimiter}esql_command{tuple_delimiter}SORT orders slow shards by delay so analysts can prioritize remediation.{tuple_delimiter}sort_field:avg_delay, order:desc){record_delimiter}
("Entity"{tuple_delimiter}where_delay_filter{tuple_delimiter}esql_concept{tuple_delimiter}A WHERE clause isolates shard metrics exceeding 1500 ms delay.{tuple_delimiter}threshold:1500_ms, focus:critical_latency){record_delimiter}
("Entity"{tuple_delimiter}cluster_routing_checklist{tuple_delimiter}best_practice{tuple_delimiter}Guided steps for mapping shard ids to cluster routing filters and validating node health.{tuple_delimiter}actions:inspect_allocation_filter|rebalance_shards){record_delimiter}
("Entity"{tuple_delimiter}macro_debug_steps{tuple_delimiter}troubleshooting_tip{tuple_delimiter}Steps for confirming LET definitions expand correctly and that slowlog fields are available.{tuple_delimiter}verification:macro_preview|field_caps){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}investigate_slow_search{tuple_delimiter}let_macro{tuple_delimiter}The troubleshooting flow relies on LET to encapsulate shard delay calculations.{tuple_delimiter}macro_reuse,latency_analysis{tuple_delimiter}8){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}let_macro{tuple_delimiter}macro_debug_steps{tuple_delimiter}Debug steps ensure the macro renders accurate shard metrics before further analysis.{tuple_delimiter}macro_validation,field_checks{tuple_delimiter}7){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}where_delay_filter{tuple_delimiter}cluster_routing_checklist{tuple_delimiter}Filtering to high-delay shards guides routing checks that uncover overloaded nodes.{tuple_delimiter}targeted_investigation,shard_rebalance{tuple_delimiter}8){record_delimiter}
("High-level keywords"{tuple_delimiter}slowlog_analysis, esql_macros, shard_latency, cluster_routing){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}investigate_slow_search{tuple_delimiter}let_macro{tuple_delimiter}sort_command{tuple_delimiter}where_delay_filter{tuple_delimiter}cluster_routing_checklist{tuple_delimiter}macro_debug_steps{tuple_delimiter}These elements outline a repeatable latency triage playbook: define a macro, rank delays, filter critical shards, and confirm routing on affected nodes.{tuple_delimiter}search_latency_troubleshooting_cycle{tuple_delimiter}macro_workflows,latency_filters,node_validation{tuple_delimiter}9){completion_delimiter}
#############################""",
    """Example 5:

Entity_types: [esql_concept, esql_command, function_reference, configuration_option, use_case, troubleshooting_tip, integration_point, best_practice]
Text:
Title: Prepare ES|QL data for executive summaries
Breadcrumbs: Enablement > ES|QL Tutorials > Storytelling
Main_content: Use the FROM clause to pull product.analytics summaries and apply RENAME to clarify column headers before exporting results to CSV. Wrap long narrative fields with TRIM to remove extraneous whitespace so business stakeholders can read concise insights. Highlight how CASE statements tag revenue tiers for each product line.
################
Output:
("Entity"{tuple_delimiter}prepare_executive_summary{tuple_delimiter}use_case{tuple_delimiter}Tutorial explaining how analysts format ES|QL outputs for executive-ready storytelling artifacts.{tuple_delimiter}doc_title:Prepare ES|QL data for executive summaries, output_format:csv){record_delimiter}
("Entity"{tuple_delimiter}from_clause_usage{tuple_delimiter}esql_concept{tuple_delimiter}FROM selects product.analytics data as the foundation for summary narratives.{tuple_delimiter}source_index:product.analytics, selection_scope:aggregated){record_delimiter}
("Entity"{tuple_delimiter}rename_command{tuple_delimiter}esql_command{tuple_delimiter}RENAME adjusts field names to be executive-friendly in exported reports.{tuple_delimiter}examples:revenue.gross->gross_revenue|narrative.long->summary_text){record_delimiter}
("Entity"{tuple_delimiter}trim_function{tuple_delimiter}function_reference{tuple_delimiter}TRIM cleans lengthy description fields so CSV exports remain readable.{tuple_delimiter}target_fields:summary_text, benefit:remove_whitespace){record_delimiter}
("Entity"{tuple_delimiter}case_revenue_tiers{tuple_delimiter}esql_concept{tuple_delimiter}CASE statements categorize products into revenue tiers for quick stakeholder scanning.{tuple_delimiter}tiers:platinum|gold|growth){record_delimiter}
("Entity"{tuple_delimiter}csv_export_guideline{tuple_delimiter}best_practice{tuple_delimiter}Recommendations for exporting ES|QL tables with consistent headers, sanitized text, and explanatory annotations.{tuple_delimiter}audience:executive_readers, documentation:storytelling_checklist){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}prepare_executive_summary{tuple_delimiter}rename_command{tuple_delimiter}Renaming columns is key to translating raw analytics into executive language.{tuple_delimiter}reporting_clarity,field_labeling{tuple_delimiter}8){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}trim_function{tuple_delimiter}csv_export_guideline{tuple_delimiter}TRIM supports the export guideline by ensuring text fields remain tidy in CSV files.{tuple_delimiter}data_cleaning,export_quality{tuple_delimiter}7){record_delimiter}
("Low-order Hyperedge"{tuple_delimiter}case_revenue_tiers{tuple_delimiter}prepare_executive_summary{tuple_delimiter}Revenue tiers enrich the summary narrative with categorical insights for leadership decisions.{tuple_delimiter}business_storytelling,revenue_analysis{tuple_delimiter}8){record_delimiter}
("High-level keywords"{tuple_delimiter}executive_reporting, esql_formatting, case_statements, csv_exports){record_delimiter}
("High-order Hyperedge"{tuple_delimiter}prepare_executive_summary{tuple_delimiter}from_clause_usage{tuple_delimiter}rename_command{tuple_delimiter}trim_function{tuple_delimiter}case_revenue_tiers{tuple_delimiter}csv_export_guideline{tuple_delimiter}This association captures the storytelling pipeline: select analytics data, rename for clarity, trim narratives, categorize revenue, and package everything for CSV delivery.{tuple_delimiter}executive_storytelling_flow{tuple_delimiter}data_selection,formatting_best_practices,business_contextualization{tuple_delimiter}8){completion_delimiter}
#############################""",
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

You are a helpful assistant responding to questions about data in the tables provided.


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.

---Target response length and format---

{response_type}

---Data tables---

{context_data}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown.
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

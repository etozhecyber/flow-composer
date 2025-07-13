<details>
<summary>Flow Details</summary>

**Analyzer:** analyze the current game situation, validate player actions, and determine outcomes

```json
{{analyzer | tojson(indent=2)}}
```

**Planner:** design NPC reactions, prepare narrative output, and craft engaging narration

```json
{{planner | tojson(indent=2)}}
```

**Actor:** deliver the scene narration and perform one main NPC character in detail

```json
{{actor | tojson(indent=2)}}
```

</details>

{% if formatter %}
{{formatter.response}}
{% else %}
*Thinking...*
{% endif %}

**CHARACTER INFORMATION:**

**MAIN CHARACTER:**
- Name: {{cast.active.name}}
- Description: {{cast.active.description}}

**NPCS IN SCENE:**
The following is a list of NPCs.
{% for npc in cast.inactive %}
- Name: {{npc.name}}
- Description: {{npc.description}}

{% endfor %}

**CONVERSATION HISTORY:**
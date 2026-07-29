"""
Halcyon Expanse — NPC Dialogue System
Branching conversations with condition checks, reputation effects, quest triggers.
"""


class DialogueNode:
    """A single node in a dialogue tree."""
    def __init__(self, node_id, speaker, text, choices=None, 
                 condition=None, on_select=None, emotion="neutral"):
        self.node_id = node_id
        self.speaker = speaker
        self.text = text
        self.choices = choices or []  # [(text, next_node_id, condition)]
        self.condition = condition  # lambda game_state: bool
        self.on_select = on_select  # lambda game_state: effect
        self.emotion = emotion  # neutral, happy, angry, sad, surprised
        self.visited = False

    def is_available(self, game_state):
        if self.condition:
            return self.condition(game_state)
        return True

    def get_available_choices(self, game_state):
        """Get choices that meet their conditions."""
        available = []
        for text, next_id, condition in self.choices:
            if condition is None or condition(game_state):
                available.append((text, next_id))
        return available


class DialogueTree:
    """A complete dialogue tree for an NPC."""
    def __init__(self, npc_name, root_node_id="start"):
        self.npc_name = npc_name
        self.nodes = {}
        self.root_node_id = root_node_id
        self.current_node_id = root_node_id

    def add_node(self, node):
        self.nodes[node.node_id] = node

    def get_current_node(self):
        return self.nodes.get(self.current_node_id)

    def select_choice(self, choice_index, game_state):
        """Process a player choice."""
        node = self.get_current_node()
        if not node:
            return None

        available = node.get_available_choices(game_state)
        if 0 <= choice_index < len(available):
            text, next_id = available[choice_index]
            self.current_node_id = next_id

            # Trigger on_select if present
            next_node = self.nodes.get(next_id)
            if next_node and next_node.on_select:
                next_node.on_select(game_state)

            return next_node
        return None

    def reset(self):
        self.current_node_id = self.root_node_id


class DialogueManager:
    """Manages all NPC dialogues."""

    def __init__(self):
        self.dialogues = {}
        self._init_default_dialogues()

    def _init_default_dialogues(self):
        """Create default NPC dialogues."""

        # Chancellor Isbeth Rowe
        isbeth = DialogueTree("Chancellor Isbeth Rowe")
        isbeth.add_node(DialogueNode("start", "Isbeth", 
            "Welcome to Concord Spire, traveler. The Lattice sings differently today.",
            choices=[
                ("What do you mean?", "lattice_explain", None),
                ("I need work.", "quests", None),
                ("Tell me about the Scar.", "vashti_info", None),
                ("Goodbye.", "end", None),
            ],
            emotion="neutral"))

        isbeth.add_node(DialogueNode("lattice_explain", "Isbeth",
            "The Lattice... it is the breath between atoms. Some hear it as song, others as static. "
            "Your Resonance determines what you hear.",
            choices=[
                ("What is my Resonance?", "resonance_check", None),
                ("Can I change it?", "resonance_change", None),
                ("Back to topics.", "start", None),
            ],
            emotion="happy"))

        isbeth.add_node(DialogueNode("quests", "Isbeth",
            "The Concord always needs capable hands. I have tasks that require someone... flexible.",
            choices=[
                ("Tell me more.", "quest_details", None),
                ("Not interested.", "start", None),
            ],
            emotion="neutral"))

        isbeth.add_node(DialogueNode("quest_details", "Isbeth",
            "First: explore the outer rings. Second: the Scar grows restless. "
            "And third... there are rumors of something ancient in the Salt Wastes.",
            choices=[
                ("I'll take the exploration task.", "quest_accept_explore", 
                 lambda gs: "tutorial_first_steps" not in [q.quest_id for q in gs.quest_manager.active_quests]),
                ("Tell me about the Scar.", "vashti_info", None),
                ("Maybe later.", "start", None),
            ],
            emotion="serious"))

        isbeth.add_node(DialogueNode("quest_accept_explore", "Isbeth",
            "Good. Walk the rings. Feel the Lattice. Return when you have seen enough.",
            choices=[
                ("I will.", "end", None),
            ],
            emotion="happy",
            on_select=lambda gs: gs.quest_manager.start_quest("tutorial_first_steps") if hasattr(gs, 'quest_manager') else None))

        isbeth.add_node(DialogueNode("vashti_info", "Isbeth",
            "The Vashti Scar... Year 518, we walled it off. The Lattice dies there. "
            "Something beneath the ruins feeds on it. The Ferro Compact salvages what they can.",
            choices=[
                ("Can I enter?", "vashti_permit", None),
                ("What feeds on Lattice?", "vashti_horror", None),
                ("Back.", "start", None),
            ],
            emotion="sad"))

        isbeth.add_node(DialogueNode("vashti_permit", "Isbeth",
            "Speak to Foreman Dask at the Wall gatehouse. He issues permits... for a price.",
            choices=[
                ("I'll find him.", "end", None),
            ],
            emotion="neutral"))

        isbeth.add_node(DialogueNode("end", "Isbeth",
            "Walk carefully, traveler. The Expanse does not forgive the careless.",
            choices=[],
            emotion="neutral"))

        self.dialogues["isbeth_rowe"] = isbeth

        # Warden Nell Achera
        nell = DialogueTree("Warden Nell Achera")
        nell.add_node(DialogueNode("start", "Nell",
            "*She watches you with eyes that have seen too much* "
            "You smell like the Spire. Bureaucracy and incense.",
            choices=[
                ("Who are you?", "nell_intro", None),
                ("I heard you were excommunicated.", "nell_exile", None),
                ("Can you teach me?", "nell_teach", None),
                ("Leave.", "end", None),
            ],
            emotion="neutral"))

        nell.add_node(DialogueNode("nell_intro", "Nell",
            "I am what remains of the Hollow Choir's truth-seekers. "
            "They cast me out for asking questions they feared.",
            choices=[
                ("What questions?", "nell_questions", None),
                ("Join me.", "nell_join", lambda gs: gs.player.attunement_level >= 3),
                ("Back.", "start", None),
            ],
            emotion="sad"))

        nell.add_node(DialogueNode("nell_join", "Nell",
            "*A ghost of a smile* You have strength. I will walk with you... for now.",
            choices=[
                ("Welcome.", "end", None),
            ],
            emotion="happy"))

        nell.add_node(DialogueNode("end", "Nell",
            "The void whispers. Listen... or don't. Your choice.",
            choices=[], emotion="neutral"))

        self.dialogues["nell_achera"] = nell

        # Foreman Dask Ilyrian
        dask = DialogueTree("Foreman Dask Ilyrian")
        dask.add_node(DialogueNode("start", "Dask",
            "Permits. Salvage. Repairs. The Wall doesn't maintain itself. What do you need?",
            choices=[
                ("Scar permit.", "permit_request", None),
                ("Buy salvage.", "shop", None),
                ("What do you find in there?", "salvage_info", None),
                ("Leave.", "end", None),
            ],
            emotion="neutral"))

        dask.add_node(DialogueNode("permit_request", "Dask",
            "Scar entry? 50 CS. Non-negotiable. The Concord doesn't subsidize curiosity.",
            choices=[
                ("Here. [Pay 50 CS]", "permit_paid", lambda gs: gs.economy.get_balance('CS') >= 50),
                ("Too expensive.", "start", None),
            ],
            emotion="neutral"))

        dask.add_node(DialogueNode("permit_paid", "Dask",
            "*Counts the scrip* Right. Don't die. I hate paperwork.",
            choices=[
                ("Thanks.", "end", None),
            ],
            emotion="neutral",
            on_select=lambda gs: gs.economy.exchange('CS', 'LM', 50) if hasattr(gs, 'economy') else None))

        dask.add_node(DialogueNode("end", "Dask",
            "Watch your step. The Scar takes the unwary.",
            choices=[], emotion="neutral"))

        self.dialogues["dask_ilyrian"] = dask

    def get_dialogue(self, npc_id):
        return self.dialogues.get(npc_id)

    def talk_to(self, npc_id, game_state):
        """Start or continue dialogue with an NPC."""
        dialogue = self.get_dialogue(npc_id)
        if not dialogue:
            return None, f"{npc_id} has nothing to say."

        node = dialogue.get_current_node()
        if not node:
            return None, "Dialogue ended."

        node.visited = True
        choices = node.get_available_choices(game_state)

        return node, choices

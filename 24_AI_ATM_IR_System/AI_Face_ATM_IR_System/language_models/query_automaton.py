import re

class QueryAutomaton:
    """
    Deterministic Finite Automaton (DFA) for validating Information Retrieval queries.
    Grammar:
        Query -> [NOT] Term ((AND | OR) [NOT] Term)*
        Supports Boolean operators: AND, OR, NOT
    States:
        S0: START
        S1: EXPECT_TERM (after NOT or binary operator)
        S2: TERM_FOUND (valid terminal candidate)
        S3: OPERATOR_FOUND (after AND / OR)
        S4: ERROR / REJECT
        S5: ACCEPT (final accepting state)
    """

    def __init__(self):
        self.operators = {"AND", "OR"}
        self.unary = {"NOT"}

    def tokenize(self, query_str: str):
        # Match words, operators, or quotes
        tokens = []
        raw_tokens = re.findall(r'[a-zA-Z0-9_\-\.\*]+|\(|\)', query_str.strip())
        for t in raw_tokens:
            tokens.append(t)
        return tokens

    def process(self, query_str: str):
        tokens = self.tokenize(query_str)
        if not tokens:
            return {
                "valid": False,
                "states_traversed": ["START", "REJECT"],
                "transitions": [{"from": "START", "input": "<EMPTY>", "to": "REJECT"}],
                "tokens": [],
                "reason": "Empty query provided.",
                "accepted": False
            }

        state = "START"
        states_traversed = [state]
        transitions = []

        for idx, token in enumerate(tokens):
            upper_token = token.upper()
            from_state = state

            if state == "START":
                if upper_token in self.unary:
                    state = "EXPECT_TERM"
                elif upper_token not in self.operators:
                    state = "TERM_FOUND"
                else:
                    state = "REJECT"
            elif state == "EXPECT_TERM":
                if upper_token not in self.operators and upper_token not in self.unary:
                    state = "TERM_FOUND"
                else:
                    state = "REJECT"
            elif state == "TERM_FOUND":
                if upper_token in self.operators:
                    state = "OPERATOR_FOUND"
                elif upper_token not in self.unary:
                    # Implicit AND between terms: e.g. "face recognition"
                    state = "TERM_FOUND"
                else:
                    state = "REJECT"
            elif state == "OPERATOR_FOUND":
                if upper_token in self.unary:
                    state = "EXPECT_TERM"
                elif upper_token not in self.operators:
                    state = "TERM_FOUND"
                else:
                    state = "REJECT"
            else:
                state = "REJECT"

            transitions.append({
                "from": from_state,
                "input": token,
                "to": state,
                "step": idx + 1
            })
            states_traversed.append(state)

            if state == "REJECT":
                break

        accepted = (state == "TERM_FOUND")
        if accepted:
            states_traversed.append("ACCEPT")
            transitions.append({
                "from": state,
                "input": "<EOF>",
                "to": "ACCEPT",
                "step": len(tokens) + 1
            })

        reason = "Query syntax successfully accepted by automaton." if accepted else f"Syntax error at or near '{token}' in state '{from_state}'."

        return {
            "valid": accepted,
            "accepted": accepted,
            "final_state": "ACCEPT" if accepted else "REJECT",
            "states_traversed": states_traversed,
            "transitions": transitions,
            "tokens": tokens,
            "reason": reason
        }

import re


class ItemMatchingRule:
    ...


class StatementInfo:
    position: tuple[int, int]
    check_rule: ItemMatchingRule
    placeholder: bool

    def __init__(self, position: tuple[int, int], check_rule: ItemMatchingRule, placeholder: bool = False) -> None:
        self.position = position
        self.check_rule = check_rule
        self.placeholder = placeholder


class AnyRegexFulfilled(ItemMatchingRule):
    regexs: tuple[re.Pattern]

    def __init__(self, *regexs: str) -> None:
        self.regexs = compileListOfRegex(regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="trigger")


class ReachPercentage(ItemMatchingRule):
    regexs: list[re.Pattern]
    percentage: float  # from 0.0 to 100.0

    def __init__(self, regexs: list[str], percentage: float) -> None:
        self.regexs = compileListOfRegex(regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="trigger")
        self.percentage = percentage


class NearbyPageMatching(ItemMatchingRule):
    """
    Search in previous or next page.
    """
    trigger_regexs: list[re.Pattern]
    search_nearby_regexs: list[re.Pattern]

    def __init__(self, trigger_regexs: list[str], search_nearby_regexs: list[str]) -> None:
        self.trigger_regexs = compileListOfRegex(
            trigger_regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="trigger"
        )
        self.search_nearby_regexs = compileListOfRegex(
            search_nearby_regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="nearby"
        )


class NearbyCharMatching(ItemMatchingRule):
    """
    Search near n sentences.
    """
    trigger_regexs: list[re.Pattern]
    search_nearby_regexs: list[re.Pattern]
    near_n_char: int

    def __init__(self, trigger_regexs: list[str], search_nearby_regexs: list[str], near_n_char: int) -> None:
        self.trigger_regexs = compileListOfRegex(
            trigger_regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="trigger"
        )
        self.search_nearby_regexs = compileListOfRegex(
            search_nearby_regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="nearby"
        )
        self.near_n_char = near_n_char


def compileListOfRegex(regex_str_list: list[str], flags: re.RegexFlag, naming_capturing: str | None = None) -> list[re.Pattern]:
    if naming_capturing == None:
        return [re.compile(regex_str, flags=flags) for regex_str in regex_str_list]
    else:
        return [re.compile("(?P<" + naming_capturing + ">" + regex_str + ")", flags=flags) for regex_str in regex_str_list]


statement_dict: dict[str, StatementInfo] = {
    "statement_by_chairman": StatementInfo(
        position=(0, 3),
        check_rule=ReachPercentage([
            # Match the title
            "(?:letter|note|message)\\s+from\\s+.*\s+(?:ceo|president|chairman)?",
            # Endings
            "(?:regards?|sincere(?:ly)?),?"
        ], percentage=48),
        placeholder=True
    ),
    "report_code_violation": StatementInfo(
        position=(0, 5),
        check_rule=AnyRegexFulfilled(
            "investigate", "report.+(?:concern|issue)", "hotline", "anonymous", "retaliation"
        )
    ),
    "sox_406": StatementInfo(
        position=(0, 6),
        check_rule=AnyRegexFulfilled("oxley", "(?:section|SOX) 406")
    ),
    "honesty": StatementInfo(
        position=(0, 9),
        check_rule=AnyRegexFulfilled("honesty?")
    ),
    "fairness": StatementInfo(
        position=(0, 10),
        check_rule=AnyRegexFulfilled("\\bfair(?:ness)?\\b")
    ),
    "integrity": StatementInfo(
        position=(0, 11),
        check_rule=AnyRegexFulfilled("integrity")
    ),
    "loyalty": StatementInfo(
        position=(0, 12),
        check_rule=AnyRegexFulfilled("loyalty", "faithful")
    ),
    "due_care": StatementInfo(
        position=(0, 13),
        check_rule=AnyRegexFulfilled("duty")
    ),
    "compliance": StatementInfo(
        position=(0, 14),
        check_rule=NearbyPageMatching(
            trigger_regexs=["comply"],
            search_nearby_regexs=["law", "regulation"]
        )
    ),
    "conflict": StatementInfo(
        position=(0, 15),
        check_rule=AnyRegexFulfilled("conflicts?\\s+of\\s+interest")
    ),
    "assets": StatementInfo(
        position=(0, 16),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=["asset", "property", "equipment"]
        )
    ),
    "confidential": StatementInfo(
        position=(0, 17),
        check_rule=AnyRegexFulfilled("confidential")
    ),
    "prohibit_cash_gift": StatementInfo(
        position=(0, 19),
        check_rule=AnyRegexFulfilled("cash")
    ),
    "stipulated_limit_cash": StatementInfo(
        position=(0, 20),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\$"],
            search_nearby_regexs=["gift", "entertainment"]
        )
    ),
    "gift_disclose": StatementInfo(
        position=(0, 21),
        check_rule=NearbyCharMatching(
            trigger_regexs=["gift"],
            search_nearby_regexs=["disclose", "disclosure"],
            near_n_char=60
        )
    ),
    "giftnominal": StatementInfo(
        position=(0, 22),
        check_rule=AnyRegexFulfilled(
            r"gift.*\bnominal\b", r"gift.*\blogo\b",
        )
    ),
    # "giftnominal": StatementInfo(
    #    position=(0, 22),
    #    check_rule=NearbyPageMatching(
    #        trigger_regexs=["gift"],
    #        search_nearby_regexs=["nominal", "logo"]
    #    )
    # ),
    "conflict_a": StatementInfo(
        position=(1, 3),
        check_rule=AnyRegexFulfilled("conflicts?\\s+of\\s+interest")
    ),
    "conflict_b": StatementInfo(
        position=(1, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["interest"],
            search_nearby_regexs=["company"]
        )
    ),
    "conflict_c": StatementInfo(
        position=(1, 5),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?\\s+of\\s+interest"],
            search_nearby_regexs=["disclose", "disclosure"]
        )
    ),
    "conflict_d1": StatementInfo(
        position=(1, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?\\s+of\\s+interest"],
            search_nearby_regexs=["family.+(?:competitor|third|financial\\s+interest|supplier|franchise)"]
        )
    ),
    "conflict_d2": StatementInfo(
        position=(1, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?\\s+of\\s+interest"],
            search_nearby_regexs=[
                "serv(?:e|ing|ice)\\s+as.+(?:director|officer|partner|consult|contactor|competitor)", "outside\\s+ employ.+(?:director|officer|partner|consult|contactor|competitor)"
            ]
        )
    ),
    "conflict_d3": StatementInfo(
        position=(1, 9),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?\\s+of\\s+interest"],
            search_nearby_regexs=[
                "serv(?:e|ing|ice)\\s+ as.+(?:broker|finder|intermediary|third\\s+party)", "outside\\s+ employ.+(?:broker|finder|intermediary|third\\s+party)"
            ]

        )
    ),
    "conflict_d4": StatementInfo(
        position=(1, 10),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?\\s+of\\s+interest"],
            search_nearby_regexs=["family", "friend"]
        )
    ),
    "conflict_e": StatementInfo(
        position=(1, 11),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?\\s+of\\s+interest"],
            search_nearby_regexs=["sign\\s+annually"]
        )
    ),
    "assets_a": StatementInfo(
        position=(1, 13),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=["asset", "property", "equipment"]
        )
    ),
    "assets_b": StatementInfo(
        position=(1, 14),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=[r"(?:physical|tangible)", "equipment", "material", "inventory"]
        )
    ),
    "assets_c": StatementInfo(
        position=(1, 15),
        check_rule=NearbyCharMatching(
            trigger_regexs=["confidential", r"\bdata\b"],
            search_nearby_regexs=["protect", "safeguard"],
            near_n_char=150
        )
    ),
    "record_a": StatementInfo(
        position=(2, 3),
        check_rule=NearbyPageMatching(
            trigger_regexs=["accurate", "complete"],
            search_nearby_regexs=["record", "book", "information", "report", "disclosure"],
        )
    ),
    "record_b": StatementInfo(
        position=(2, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["record", "book", "information", "report", "disclosure"],
            search_nearby_regexs=["improper", "misleading", "incomplete", "fraudulent", "inaccurate", "false"],
        )
    ),
    "record_c": StatementInfo(
        position=(2, 5),
        check_rule=NearbyPageMatching(
            trigger_regexs=["accounting", "defe(?:r|rring)"],
            search_nearby_regexs=["(?:follow|comply)\\s.+(?:law|polic|principle|gaap)", "misclassifications",
                                  "improperly\\s+accelerating", "defe(?:r|rring)\\s+expenses", "defe(?:r|rring)\\s+revenues"],
        )

    ),
    "record_d": StatementInfo(
        position=(2, 6),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["fair", "accurate"]
        )
    ),
    "record_e": StatementInfo(
        position=(2, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["full", "complete"]
        )
    ),
    "record_f": StatementInfo(
        position=(2, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["timely", "up\\s+to\\s+date"]
        )
    ),
    "record_g": StatementInfo(
        position=(2, 9),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["understandable"]
        )
    ),
    "compliance_a": StatementInfo(
        position=(2, 11),
        check_rule=AnyRegexFulfilled("Investigate", "report concern", "report issue",
                                     "hotline", "anonymous", "retaliation")
    ),
    "compliance_b": StatementInfo(
        position=(2, 12),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report"],
            search_nearby_regexs=["hotline", "anonymous"]
        )
    ),
    "compliance_c": StatementInfo(
        position=(2, 13),
        check_rule=AnyRegexFulfilled("anonymous")

    ),
    "compliance_d": StatementInfo(
        position=(2, 14),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\breport"],
            search_nearby_regexs=["terminat(?:e|ing)", "consequence\\s+violat", "\\discharge\\b", "criminal"]
        )
    ),
    "compliance_e": StatementInfo(
        position=(2, 15),
        check_rule=AnyRegexFulfilled("retaliation", "retaliate")

    ),
    "compliance_f": StatementInfo(
        position=(2, 16),
        check_rule=AnyRegexFulfilled("waiver")

    ),
    "compliance_g": StatementInfo(
        position=(2, 17),
        check_rule=NearbyPageMatching(
            trigger_regexs=["code"],
            search_nearby_regexs=["review.+(period, every)"]
        )
    ),
    "travel_a": StatementInfo(
        position=(3, 3),
        check_rule=AnyRegexFulfilled("travel", "entertainment")

    ),
    "travel_b": StatementInfo(
        position=(3, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["travel", "entertainment"],
            search_nearby_regexs=["money\\s+careful"]
        )
    ),
    "travel_c": StatementInfo(
        position=(3, 5),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\btravel\\b", "entertainment"],
            search_nearby_regexs=["\\bgain\\b", "\\blose\\b"]
        )
    ),
    "political_a": StatementInfo(
        position=(3, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=["company\\s+resource"]
        )
    ),
    "political_b": StatementInfo(
        position=(3, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=["committee", "activity", "organization"]
        )
    ),
    "political_c": StatementInfo(
        position=(3, 9),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=["pressure", "free"]
        )
    ),
    "equal_a": StatementInfo(
        position=(3, 11),
        check_rule=NearbyPageMatching(
            trigger_regexs=["respect"],
            search_nearby_regexs=["culture", "difference", "right"]
        )
    ),
    "equal_b": StatementInfo(
        position=(3, 12),
        check_rule=AnyRegexFulfilled("\\brace\\b", "religion", "national\\s+origin", "\\bsex\\b")

    ),
    "equal_c": StatementInfo(
        position=(3, 13),
        check_rule=NearbyPageMatching(
            trigger_regexs=["haras(?:s|sment)"],
            search_nearby_regexs=["tolerate", "forbidden", "prohibit"]
        )

    ),
    "anti_a": StatementInfo(
        position=(3, 15),
        check_rule=AnyRegexFulfilled("antitrust")

    ),
    "anti_b": StatementInfo(
        position=(3, 16),
        check_rule=NearbyPageMatching(
            trigger_regexs=["antitrust"],
            search_nearby_regexs=["measure.+(violate)", "ensure.+(law)"]
        )
    ),
    "gov_a": StatementInfo(
        position=(3, 18),
        check_rule=NearbyPageMatching(
            trigger_regexs=["foreign"],
            search_nearby_regexs=["government", "offical"]
        )
    ),
    "gov_b": StatementInfo(
        position=(3, 19),
        check_rule=NearbyPageMatching(
            trigger_regexs=["government", "offical"],
            search_nearby_regexs=["bribery", "prohibit.+(meal, courtes(?:y|ies), entertainment)"]
        )
    ),
    "inducement_a": StatementInfo(
        position=(4, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["sale"],
            search_nearby_regexs=["tax"]
        )
    ),
    "inducement_b": StatementInfo(
        position=(4, 5),
        check_rule=NearbyCharMatching(
            trigger_regexs=["payment"],
            search_nearby_regexs=["reasonable", "meaningful", "justified", "properly"],
            near_n_char=7
        )
    ),
    "inducement_c": StatementInfo(
        position=(4, 6),
        check_rule=NearbyPageMatching(
            trigger_regexs=["payment.+(sale)"],
            search_nearby_regexs=["within.+(country, state, federal)"]
        )
    ),
    "inducement_d": StatementInfo(
        position=(4, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["payment.+(purchase)"],
            search_nearby_regexs=["within.+(country, state, federal)"]
        )
    ),
    "inducement_e": StatementInfo(
        position=(4, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["1977", "corrupt"],
            search_nearby_regexs=["1988", "omnibus"]
        )
    ),
    "inducement_f": StatementInfo(
        position=(4, 9),
        check_rule=NearbyCharMatching(
            trigger_regexs=["payment"],
            search_nearby_regexs=["legal", "necessary", "meaningful", "reasonable", "proper"],
            near_n_char=7
        )
    ),
    "insider_a": StatementInfo(
        position=(4, 11),
        check_rule=AnyRegexFulfilled("insider?\\s+(?:information|trad(?:e|ing))\\b")

    ),
    "insider_b": StatementInfo(
        position=(4, 12),
        check_rule=NearbyPageMatching(
            trigger_regexs=["confidential", "insid(?:e|er)"],
            search_nearby_regexs=["personal\\s+gain", "personal\\s+profit"]
        )
    ),
    "insider_c": StatementInfo(
        position=(4, 13),
        check_rule=NearbyPageMatching(
            trigger_regexs=["confidential", "insid(?:e|er)"],
            search_nearby_regexs=["stock", "securit(?:y|ies)"]
        )
    ),
    "boycott_a": StatementInfo(
        position=(5, 3),
        check_rule=AnyRegexFulfilled("boycott")

    ),
    "competitive_a": StatementInfo(
        position=(5, 6),
        check_rule=NearbyPageMatching(
            trigger_regexs=["data"],
            search_nearby_regexs=["collect.+(competitor)"]
        )
    ),
    "competitive_b": StatementInfo(
        position=(5, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["data"],
            search_nearby_regexs=["prohibit.+(competitor)"]
        )
    ),
    "polotical2_a": StatementInfo(
        position=(5, 11),
        check_rule=NearbyPageMatching(
            trigger_regexs=["offical", "government"],
            search_nearby_regexs=["Corrupt", "bribe"]
        )
    ),
    "polotical2_b": StatementInfo(
        position=(5, 12),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=["company\\s+resource.+(sale, induce, influence)"]
        )
    ),
    "estate_a": StatementInfo(
        position=(5, 14),
        check_rule=AnyRegexFulfilled("Estate", "natural\\s+resources")

    ),
    "estate_b": StatementInfo(
        position=(5, 15),
        check_rule=NearbyPageMatching(
            trigger_regexs=["Estate", "natural\\s+resources"],
            search_nearby_regexs=["Company\\s+resource"]
        )
    ),
    "harass": StatementInfo(
        position=(5, 17),
        check_rule=AnyRegexFulfilled("harassment")

    ),
    "estate_": StatementInfo(
        position=(5, 15),
        check_rule=NearbyPageMatching(
            trigger_regexs=["Estate", "natural\\s+resources"],
            search_nearby_regexs=["Company\\s+resource"]
        )
    ),
}

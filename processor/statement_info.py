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

    def __init__(self, trigger_regexs: list[str], search_nearby_regexs: list[str],
                 *, search_page_before:bool=True,search_page_after:bool=True) -> None:
        self.trigger_regexs = compileListOfRegex(
            trigger_regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="trigger"
        )
        self.search_nearby_regexs = compileListOfRegex(
            search_nearby_regexs, flags=re.IGNORECASE | re.MULTILINE, naming_capturing="nearby"
        )
        self.search_page_before=search_page_before
        self.search_page_after=search_page_after



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
            "(?:letter|note|message).{1,10}from.{1,10}.*\s+(?:ceo|president|chairman)?",
            # Endings
            "(?:regards?|sincere(?:ly)?),?"
        ], percentage=48),
        placeholder=True
    ),
    "report_code_violation": StatementInfo(
        position=(0, 5),
        check_rule=AnyRegexFulfilled(
            "investigate", "report.{1,30}(?:concern|issue)", "hotline", "anonymous", "retaliation"
        )
    ),
    "sox_406": StatementInfo(
        position=(0, 6),
        check_rule=AnyRegexFulfilled("oxley", "(?:section|SOX) 406")
    ),
    "honesty": StatementInfo(
        position=(0, 9),
        check_rule=AnyRegexFulfilled("honesty?", "\\bintegrity\\b","\\bgenuine\\b", "\\bsincere\\b", "\\btruthful\\b", 
        "\\btrustworthy\\b", "\\btrusty\\b","\\bfrank\\b", "\\bdecent\\b", "\\bupright\\b", "\\breliable\\b"  )
    ),
    "fairness": StatementInfo(
        position=(0, 10),
        check_rule=AnyRegexFulfilled("\\bfair(?:ness)?\\b")
    ),
    "integrity": StatementInfo(
        position=(0, 11),
        check_rule=AnyRegexFulfilled("integrity", "honesty?", "\\bupright", "\\bprobity\\b")
    ),
    "loyalty": StatementInfo(
        position=(0, 12),
        check_rule=AnyRegexFulfilled("loyalty", "faithful", "allegiance", "devot(?:e|ion)")
    ),
    "due_care": StatementInfo(
        position=(0, 13),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=["assets?", "propert(?:y|ies)", "equipments?"]
        )
    ),
    "compliance": StatementInfo(
        position=(0, 14),
        check_rule=NearbyPageMatching(
            trigger_regexs=["compl(?:y|iance)","follow"], 
            search_nearby_regexs=["law", "regulation"]
        )
    ),
    "conflict": StatementInfo(
        position=(0, 15),
        check_rule=AnyRegexFulfilled("conflicts?.{1,5}of.{1,5}interest")
    ),
    "assets": StatementInfo(
        position=(0, 16),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=["assets?", "propert(?:y|ies)", "equipments?"]
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
            search_nearby_regexs=["gift", "entertainment", "\\bmore.{1,5}than","\\bless.{1,5}than"]
        )
    ),
    "gift_disclose": StatementInfo(
        position=(0, 21),
        check_rule=NearbyCharMatching(
            trigger_regexs=["gift"],
            search_nearby_regexs=["disclos(?:e|ure)", "notify","contact"],
            near_n_char=200
        )
    ),
    "giftnominal": StatementInfo(
        position=(0, 22),
        check_rule=NearbyPageMatching(
            trigger_regexs=["gift"],
            search_nearby_regexs=[r"\bnominal\b", r"\blogo\b"],
            search_page_before=False, search_page_after=False
        )
    ),
    "conflict_a": StatementInfo(
        position=(1, 3),
        check_rule=AnyRegexFulfilled("conflicts?.{1,5}of.{1,5}interests?")
    ),
    "conflict_b": StatementInfo(
        position=(1, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["interests?"],
            search_nearby_regexs=["company","organization","corporat(?:e|ion)"],
            search_page_before=False, search_page_after=False
        )
    ),
    "conflict_c": StatementInfo(
        position=(1, 5),
        check_rule=NearbyPageMatching(
            trigger_regexs=["disclose", "disclosure"],
            search_nearby_regexs=["conflicts?.{1,5}of.{1,5}interests?"],
            search_page_before=False, search_page_after=False
        )
    ),
    "conflict_d1": StatementInfo(
        position=(1, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?.{1,5}of.{1,5}interests?"],
            search_nearby_regexs=["(?:famil(?:y|ies)|relatives?)\\b.{1,60}(?:competitor|third|financial.{1,5}interest|supplier|franchise)"]
        )
    ),
    "conflict_d2": StatementInfo(
        position=(1, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?.{1,5}of.{1,5}interests?"],
            search_nearby_regexs=[
                "serv(?:e|ing|ice).{1,15}as.{1,10}(?:director|officer|partner|consult|contactor|competitor|supervisor|supervisory|supervising)",
                "outside.{1,15}employ.{1,30}(?:director|officer|partner|consult|contactor|competitor|supervisor|supervisory|supervising)"
            ]
        )
    ),
    "conflict_d3": StatementInfo(
        position=(1, 9),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?.{1,10}of.{1,10}interests?"],
            search_nearby_regexs=[
                "serv(?:e|ing|ice).{1,20} as.{1,10}(?:broker|finder|intermediary|third.{1,5}party)",
                "outside.{1,15} employ.{1,30}(?:broker|finder|intermediary|third.{1,5}party)"
            ]

        )
    ),
    "conflict_d4": StatementInfo(
        position=(1, 10),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?.{1,5}of.{1,5}interests?"],
            search_nearby_regexs=["famil(?:y|ies)", "\\bfriend\\b", "\\brelatives?\\b"]
        )
    ),
    "conflict_e": StatementInfo(
        position=(1, 11),
        check_rule=NearbyPageMatching(
            trigger_regexs=["conflicts?.{1,5}of.{1,5}interests?"],
            search_nearby_regexs=["sign.{1,30}annually"]
        )
    ),
    "assets_a": StatementInfo(
        position=(1, 13),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=["assets?", "propert(?:y|ies)", "equipments?"]
        )
    ),
    "assets_b": StatementInfo(
        position=(1, 14),
        check_rule=NearbyPageMatching(
            trigger_regexs=["protect", "safeguard"],
            search_nearby_regexs=[r"(?:physical|tangible)", "equipments?", "\\bmaterials?\\b", "inventor(?:y|ies)"]
        )
    ),
    "assets_c": StatementInfo(
        position=(1, 15),
        check_rule=NearbyCharMatching(
            trigger_regexs=["confidential", r"\bdata\b", "information"],
            search_nearby_regexs=["protect", "safeguard"],
            near_n_char=150
        )
    ),
    "record_a": StatementInfo(
        position=(2, 3),
        check_rule=NearbyPageMatching(
            trigger_regexs=["accurate", "complete"],
            search_nearby_regexs=["record", "\\bbook", "information", "report", "disclosure"],
            search_page_before=False, search_page_after=False
        )
    ),
    "record_b": StatementInfo(
        position=(2, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["record", "book", "information", "report", "disclosure"],
            search_nearby_regexs=["\\bimproper", "misleading", "incomplete", "fraudulent", "inaccurate", "\\bfalse"],
            search_page_before=False, search_page_after=False
        )
    ),
    "record_c": StatementInfo(
        position=(2, 5),
        check_rule=NearbyPageMatching(
            trigger_regexs=["accounting", "defe(?:r|rring)"],
            search_nearby_regexs=["(?:follow|compl(?:y|iance))\\s.{1,10}(?:law|polic|principle|gaap)", "misclassifications",
                                  "improperly.{1,30}accelerating", "defe(?:r|rring).{1,30}expenses", "defe(?:r|rring).{1,30}revenues"],
            search_page_before=False, search_page_after=False                      
        )

    ),
    "record_d": StatementInfo(
        position=(2, 6),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\breport", "disclosure"],
            search_nearby_regexs=["\\bfair", "\\baccurate"],
            search_page_before=False, search_page_after=False
        )
    ),
    "record_e": StatementInfo(
        position=(2, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["full", "\\bcomplete"],
            search_page_before=False, search_page_after=False
        )
    ),
    "record_f": StatementInfo(
        position=(2, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["timely", "up\\s+to\\s+date", "proper.{1,15}period"],
            search_page_before=False, search_page_after=False
        )
    ),
    "record_g": StatementInfo(
        position=(2, 9),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report", "disclosure"],
            search_nearby_regexs=["\\bunderstandable\\b"],
            search_page_before=False, search_page_after=False
        )
    ),
    "compliance_a": StatementInfo(
        position=(2, 11),
        check_rule=AnyRegexFulfilled("Investigate", "report.{1,15}concern", "report.{1,15}issue",
                                     "hotline", "anonymous", "retaliation")
    ),
    "compliance_b": StatementInfo(
        position=(2, 12),
        check_rule=NearbyPageMatching(
            trigger_regexs=["report"],
            search_nearby_regexs=["hotline", "anonymous", "call"],
            search_page_before=False, search_page_after=False

        )
    ),
    "compliance_c": StatementInfo(
        position=(2, 13),
        check_rule=AnyRegexFulfilled("anonymous(?:ly)?")

    ),
    "compliance_d": StatementInfo(
        position=(2, 14),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\breport\\b"],
            search_nearby_regexs=["terminat(?:e|ing)", "consequence.{1,15}violat", 
            "\\discharge\\b", "criminal", "disciplinary.{1,15}action", "employ(?:ment)?.{1,15}separation"],
            search_page_before=False, search_page_after=False
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
            trigger_regexs=["\\bcode\\b"],
            search_nearby_regexs=["review.{1,40}(?:period|every)"],
            search_page_before=False, search_page_after=False
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
            search_nearby_regexs=["money.{1,40}careful"],
            search_page_before=False, search_page_after=False

        )
    ),
    "travel_c": StatementInfo(
        position=(3, 5),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\btravel\\b", "entertainment"],
            search_nearby_regexs=["\\bgain\\b", "\\blose\\b"],
            search_page_before=False, search_page_after=False

        )
    ),
    "political_a": StatementInfo(
        position=(3, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=[
                "(?:company|organization|corporat(?:e|ion)).{1,20}(?:resources?|contribution|name)",
                "(?:resources?|contribution|name).{1,20}(?:company|organization|corporat(?:e|ion))"
            ],
            search_page_before=False, search_page_after=False,
        )
    ),
    "political_b": StatementInfo(
        position=(3, 8),
        check_rule=NearbyCharMatching(
            trigger_regexs=["committee", "activity", "organization"],
            search_nearby_regexs=["political"],
            near_n_char=150,
        )
    ),
    "political_c": StatementInfo(
        position=(3, 9),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=["pressure", "\\bfree\\b"],
            search_page_before=False, search_page_after=False
        )
    ),
    "equal_a": StatementInfo(
        position=(3, 11),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\brespect"],
            search_nearby_regexs=["culture", "difference", "\\brights?"]
        )
    ),
    "equal_b": StatementInfo(
        position=(3, 12),
        check_rule=AnyRegexFulfilled("\\brace\\b", "religion", "national.{1,15}origin", "\\bsex\\b")

    ),
    "equal_c": StatementInfo(
        position=(3, 13),
        check_rule=NearbyCharMatching(
            trigger_regexs=["tolerat(?:e|ion)", "forbidden", "prohibit"],
            search_nearby_regexs=["harass?(?:ment)?"],
            near_n_char=150
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
            search_nearby_regexs=[
                "measure.{1,50}(violate)", "ensure.{1,30}(law)",
                r"(?:follow|compl(?:y|iance))\s+.{1,40}(?:law)", "not.{1,15}violat(?:e|ion).{1,15}law", "price.{1,10}fix(?:ing)?", 
            ],
            search_page_before=False, search_page_after=False
        )
    ),
    "gov_a": StatementInfo(
        position=(3, 18),
        check_rule=NearbyCharMatching(
            trigger_regexs=["foreign"],
            search_nearby_regexs=["government", "official"],
            near_n_char=150
        )
    ),
    "gov_b": StatementInfo(
        position=(3, 19),
        check_rule=NearbyPageMatching(
            trigger_regexs=["government", "official"],
            search_nearby_regexs=["\\bmeals?\\b", "courtes(?:y|ies)" ,"entertainment"],
            search_page_before=False, search_page_after=False
        )
    ),
    "inducement_a": StatementInfo(
        position=(4, 4),
        check_rule=NearbyCharMatching(
            trigger_regexs=["\\bsale\\b","\\brebate\\b", "\\bdiscount\\b", "\\bcredit\\b", "\\ballowance\\b.{1,15}programs?"],
            search_nearby_regexs=["(?:follow|compl(?:y|iance)).{1,30}(?:law|currency|regulation)"],
            near_n_char=120
        )
    ),
    "inducement_b": StatementInfo(
        position=(4, 5),
        check_rule=NearbyCharMatching(
            trigger_regexs=["payment"],
            search_nearby_regexs=["\\breasonable\\b", "\\bmeaningful\\b", "\\bjustified\\b", "\\bproperly\\b"],
            near_n_char=120
        )
    ),
    "inducement_c": StatementInfo(
        position=(4, 6),
        check_rule=NearbyPageMatching(
            trigger_regexs=["payment.{1,30}(sale)"],
            search_nearby_regexs=["within.{1,40}(country, state, federal)"],
            search_page_before=False, search_page_after=False

        )
    ),
    "inducement_d": StatementInfo(
        position=(4, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["payment.{1,30}(purchase)"],
            search_nearby_regexs=["within.{1,40}(country, \\bstate\\b, \\bfederal\\b)"],
            search_page_before=False, search_page_after=False

        )
    ),
    "inducement_e": StatementInfo(
        position=(4, 8),
        check_rule=NearbyPageMatching(
            trigger_regexs=["1977", "corrupt"],
            search_nearby_regexs=["1988", "omnibus"],
            search_page_before=False, search_page_after=False

        )
    ),
    "inducement_f": StatementInfo(
        position=(4, 9),
        check_rule=NearbyCharMatching(
            trigger_regexs=["payment"],
            search_nearby_regexs=["\\blegal\\b", "\\bnecessary\\b", "\\bmeaningful\\b", "\\breasonable\\b", "\\bproper"],
            near_n_char=120,
           
        )
    ),
    "insider_a": StatementInfo(
        position=(4, 11),
        check_rule=AnyRegexFulfilled("insider?.{1,15}(?:information|trad(?:e|ing))\\b")

    ),
    "insider_b": StatementInfo(
        position=(4, 12),
        check_rule=NearbyPageMatching(
            trigger_regexs=["confidential", "insid(?:e|er)"],
            search_nearby_regexs=["personal.{1,10}gain", "personal.{1,10}profit"]
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
    "boycott_b": StatementInfo(
        position=(5, 4),
        check_rule=NearbyPageMatching(
            trigger_regexs=["anti.{1,5}boycott"],
            search_nearby_regexs=["legal.{1,15}(?:department|counsel)"]
        )
    ),
    "competitive_a": StatementInfo(
        position=(5, 6),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\bdata\\b","information"],
            search_nearby_regexs=["(?:collect|get|gather).{1,50}(competitor)"]
        )
    ),
    "competitive_b": StatementInfo(
        position=(5, 7),
        check_rule=NearbyPageMatching(
            trigger_regexs=["\\bdata\\b","information"],
            search_nearby_regexs=["prohibit.{1,60}(competitor)","(?:gather|collect|get).{1,60}(?:improper|illegal)"]
        )
    ),
    "polotical2_a": StatementInfo(
        position=(5, 11),
        check_rule=NearbyPageMatching(
            trigger_regexs=["official", "government"],
            search_nearby_regexs=["corrupt", "bribe","lobby"]
        )
    ),
    "polotical2_b": StatementInfo(
        position=(5, 12),
        check_rule=NearbyPageMatching(
            trigger_regexs=["political"],
            search_nearby_regexs=[
            "(?:company|organization|corporat(?:e|ion)).{1,15}(?:resource|fund).{1,50}(sale|induce|influence)", 
            "on.{1,10}behalf.{1,5}of.{1,20}(?:company|organization|corporat(?:e|ion))"]
        )
    ),
    "estate_a": StatementInfo(

        position=(5, 14),
        check_rule=NearbyCharMatching(
            trigger_regexs=["estate", "natural.{1,5}resources"],
            search_nearby_regexs=["compet(?:e|ing).{1, 80}(?:company|organization|corporat(?:e|ion))"],
            near_n_char=120
        )

    ),
    "estate_b": StatementInfo(
        position=(5, 15),
        check_rule=NearbyCharMatching(
            trigger_regexs=["estate", "natural.{1,5}resources"],
            search_nearby_regexs=["(?:company|organization|corporat(?:e|ion)).{1,10}(?:resource|equipment)"],
            near_n_char=120
        )
    ),
    "harass": StatementInfo(
        position=(5, 17),
        check_rule=AnyRegexFulfilled("harassment")

    ),
  
}

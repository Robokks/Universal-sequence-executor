# AIXML Authoring Rules and Known Limitations

**Primary reference:** [`Zuehlke/labview-mcp/docs/aixml-reference.md`](https://github.com/Zuehlke/labview-mcp/blob/main/docs/aixml-reference.md).  
**Workflow reference:** [`docs/guide/aixml-workflow.md`](https://github.com/Zuehlke/labview-mcp/blob/main/docs/guide/aixml-workflow.md).  
**Tool catalog:** [`docs/guide/tools.md`](https://github.com/Zuehlke/labview-mcp/blob/main/docs/guide/tools.md).

The repository reference is an **empirical description** of NI's AI-XML dialect, not a stable, publicly standardized XSD. Re-check the target LabVIEW version and MCP backend before trusting conversion results.

## 1. What this package actually creates

- One `<VI>` element per generated file, with a required nonempty `description`.
- `<Control>` and `<Indicator>` elements with scalar `double`, `int32`, and `bool` types, values and connector indices.
- `<Constant>` elements and `<Node>` elements with documented terminal labels.
- Directed data-flow wires, represented by `uid.terminal` nets through `outputs=` and `inputs=`.
- NO XML comments, unescaped user-entered Windows paths, structures, classes, library references, typedef bindings, hardware calls or framework-specific APIs.

## 2. Why two connector-pane folders?

Connector indices are not left-to-right numbers. The default connector pane depends on the LabVIEW station's configuration. In the repository's measured mappings:

| Slot | 4815 (12 terminals) | 4833 (16 terminals) |
|---|---:|---:|
| 1st data input | 11 | 0 |
| 2nd data input | 10 | 5 |
| 3rd data input | 9 | 7 |
| 4th data input | 8 | 9 |
| 1st data output | 3 | 4 |
| 2nd data output | 2 | 6 |

**Only import the folder matching the target machine's connector pattern.** On the LabVIEW PC call `lvai_connector_pane` without arguments. If the actual pattern is neither 4815 nor 4833, extend `generator/build_aixml.py` from a verified `lvai_connector_pane` pattern mapping and regenerate. Do not change LabVIEW.ini to make this package pass.

## 3. Terminal names are literal

These nodes use documented labels including punctuation and spaces:

| Node | Inputs | Outputs |
|---|---|---|
| Add | `x`, `y` | `x+y` |
| Subtract | `x`, `y` | `x-y` |
| Multiply | `x`, `y` | `x*y` |
| Divide | `x`, `y` | `x/y` |
| Greater? | `x`, `y` | `x > y?` |
| Greater Or Equal? | `x`, `y` | `x >= y?` |
| Less? | `x`, `y` | `x < y?` |
| Equal? | `x`, `y` | `x = y?` |
| Or | `x`, `y` | `x .or. y?` |
| Select | `t`, `s`, `f` | `s? t\3Af` |
| In Range and Coerce | `upper limit`, `x`, `lower limit` | `coerced(x)`, `In Range?` |

AIXML's `\3A` is an escape inside an attribute, not XML syntax. XML also escapes `<` and `>` in attributes. The generator uses Python `ElementTree`, which escapes XML entities while preserving the literal backslash-hex form.

## 4. Critical boundary behavior

All generated `In Range and Coerce` nodes include **both** `includeLow="true"` and `includeHigh="true"`. Without those two flags, equality at the limits may be treated as out of range (per the repository's measurements). The offline tests include exact boundary cases.

## 5. Serious caveats

1. **Not an official XSD:** XML parsing alone cannot guarantee NI's AIXML service accepts the file.
2. **No layout coordinates:** Native VI block-diagram layout needs visual review after generation.
3. **Typedefs are not preserved by AIXML round trips:** Do not regenerate existing production VIs with typedefs from exports without a plan to preserve bindings. Create and bind `.ctl` types through a controlled LabVIEW process.
4. **Classes and actor lifecycle cannot be created from these files alone:** Use MCP class and Actor Framework tools on a running LabVIEW instance, followed by structural verification.
5. **AIXML conversion is a mutating operation:** It can overwrite the destination VI. Always use scratch paths and Git commits.
6. **No guarantee of preemption:** A plugin hang or ordinary actor stall cannot be treated as fail-safe. Independent RT and hardware protection remain separate.
7. **Unit correctness is external:** Numeric `double` values don't carry automatic bar/mm/N calibration checks. Enforce engineering units, metadata and preflight validation in the enclosing application.
8. **Finite numbers and sensor validity:** NaN, infinity, invalid/stale sensor status, negative tolerances and nonsensical ranges should be rejected by the Parameter Registry or configuration validator before calling the helpers.

## 6. Validation levels

| Level | Performed in this package? | Required before production? |
|---|---|---|
| XML well-formedness | **Yes** | Yes |
| Basic unique UID + net reference checking | **Yes** | Yes |
| Simulated graph evaluation | **Yes** | Yes, plus native VI execution |
| `lvai_check_aixml` | **No** | Yes |
| `lvai_validate_aixml` / NI backend | **No** | Yes |
| Scratch `lvai_generate_vi` to native binary | **No** | Yes |
| Connector pane verification | **No** | Yes |
| Native VI unit tests | **No** | Yes |
| cRIO compilation and timing verification | **No** | Yes |
| Independent hardware protection verification | **No** | Mandatory for equipment use |

## 7. References and provenance

Repository author: Zuehlke. Our package is an independent implementation artifact **informed by** the public repository's documented format and tool interfaces. It does not claim endorsement by Zuehlke or NI. No repository binary or NI proprietary VI is included.

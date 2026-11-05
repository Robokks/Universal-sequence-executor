# VI intent and documentation policy (required)

Every generated VI MUST contain a useful VI description — not merely a filename. Our staged AIXML's `<VI description="…">` maps to native VI documentation. Confirm it in **LabVIEW VI Properties → Documentation** after generation.

**Mandatory content in every VI**
- Intent / responsibility in one sentence (what it calculates or controls).
- Input connector names, types, and engineering units.
- Output connector names, types, and engineering units.
- Preconditions and error behavior / invalid data behavior.
- Corresponding SRS requirement ID(s).
- Statement of hardware side effects, if any (utilities have none).

Additionally each staged VI has `outputs/<batch>/vi_docs/<VI>.md` including test vectors, connectors, assumptions, requirement traceability, and explicitly separated offline/native evidence. A VI named `UE_Relative_Target.vi`, for instance, documents that its 2 mm `offset_mm` changes **calibrated servo/PC lever position**, not hitch travel.

The VI description is not evidence that the VI works. Native compilation, result readback, and code review remain mandatory. For more complex actor/service VIs, add front-panel documentation and section comments via validated LabVIEW scripting once their dedicated generator supports it; don't add unsupported AIXML properties or FreeLabel nodes blindly.

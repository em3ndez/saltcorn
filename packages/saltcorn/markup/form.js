const formRowWrap = (hdr, inner, error = "") => `<div class="form-group row">
    <label for="input${hdr.name}" class="col-sm-2 col-form-label">${hdr.label}</label>
    <div class="col-sm-10">
      ${inner}
      ${error}
    </div>
  </div>`;
const isdef = x => typeof x !== "undefined";

const select_options = (v, hdr) => {
  const selected = v ? v[hdr.name] : undefined;
  const isSelected = value =>
    !selected
      ? false
      : selected.length
      ? selected.includes(value)
      : value === selected;
  return (opts = hdr.options
    .map(o => {
      const label = typeof o === "string" ? o : o.label;
      const value = typeof o === "string" ? o : o.value;
      return `<option value="${value}" ${
        isSelected(value) ? "selected" : ""
      }>${label}</option>`;
    })
    .join(""));
};
const mkFormRow = (v, errors) => hdr => {
  const validClass = errors[hdr.name] ? "is-invalid" : "";
  const errorFeedback = errors[hdr.name]
    ? `<div class="invalid-feedback">${errors[hdr.name]}</div>`
    : "";
  switch (hdr.input_type) {
    case "fromtype":
      return formRowWrap(
        hdr,
        hdr.type.editAs(
          hdr.name,
          v && isdef(v[hdr.name]) ? v[hdr.name] : undefined,
          validClass
        ),
        errorFeedback
      );
    case "hidden":
      return `<input type="hidden" class="form-control ${validClass}" name="${
        hdr.name
      }" ${v ? `value="${v[hdr.name]}"` : ""}>`;
    case "select":
      const opts = select_options(v, hdr);
      return formRowWrap(
        hdr,
        `<select class="form-control ${validClass}" name="${hdr.name}" id="input${hdr.name}">${opts}</select>`,
        errorFeedback
      );
    case "ordered_multi_select":
      const mopts = select_options(v, hdr);
      return formRowWrap(
        hdr,
        `<select class="form-control ${validClass}" class="chosen-select" multiple name="${hdr.name}" id="input${hdr.name}">${mopts}</select><script>$(function(){$("#input${hdr.name}").chosen()})</script>`,
        errorFeedback
      );

    default:
      return formRowWrap(
        hdr,
        `<input type="${hdr.input_type}" class="form-control" name="${
          hdr.name
        }" id="input${hdr.name}" ${
          v && isdef(v[hdr.name]) ? `value="${v[hdr.name]}"` : ""
        }>`,
        errorFeedback
      );
  }
};

const renderForm = form =>
  mkForm(form.action, form.fields, form.values, form.submitLabel, form.errors);

const mkForm = (action, hdrs, v, submitLabel = "Save", errors = {}) => {
  const top = `<form action="${action}" method="post">`;
  //console.log(hdrs);
  const flds = hdrs.map(mkFormRow(v, errors)).join("");
  const bot = `<div class="form-group row">
  <div class="col-sm-10">
    <button type="submit" class="btn btn-primary">${submitLabel}</button>
  </div>
</div>
</form>`;
  return top + flds + bot;
};

module.exports = renderForm;
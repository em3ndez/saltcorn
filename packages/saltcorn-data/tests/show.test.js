const Table = require("../models/table");
const Field = require("../models/field");
const View = require("../models/view");
const db = require("../db");
const { plugin_with_routes, mockReqRes } = require("./mocks");
const { getState } = require("../db/state");
getState().registerPlugin("base", require("../base-plugin"));

afterAll(db.close);
beforeAll(async () => {
  await require("../db/reset_schema")();
  await require("../db/fixtures")();
});

const test_show = async ({ columns, layout, response }) => {
  const table = await Table.findOne({ name: "books" });

  const v = await View.create({
    table_id: table.id,
    name: "testshow",
    viewtemplate: "Show",
    configuration: { columns, layout },
    min_role: 10,
    on_root_page: true,
  });

  const res = await v.run({ id: 1 }, mockReqRes);
  expect(res).toBe(response);
  await v.delete();
};

describe("Show view", () => {
  it("should render exactly", async () => {
    await test_show({
      layout: { type: "blank", contents: "Hello world", isFormula: {} },
      columns: [],
      response: `Hello world`,
    });
    await test_show({
      layout: { type: "field", fieldview: "as_text", field_name: "author" },
      columns: [{ type: "Field", fieldview: "as_text", field_name: "author" }],
      response: `Herman Melville`,
    });
    await test_show({
      layout: {
        type: "field",
        fieldview: "as_text",
        textStyle: "h3",
        field_name: "author",
      },
      columns: [{ type: "Field", fieldview: "as_text", field_name: "author" }],
      response: `<span class="h3">Herman Melville</span>`,
    });
    await test_show({
      layout: {
        widths: [6, 6],
        besides: [
          {
            stat: "Count",
            type: "aggregation",
            agg_field: "name",
            agg_relation: "patients.favbook",
          },
          {
            type: "action",
            rndid: "1a8ac3",
            minRole: 10,
            isFormula: {},
            action_name: "run_js_code",
            action_size: "btn-sm",
            action_label: "you're my number",
            action_style: "btn-success",
            configuration: { code: 'console.log("1")' },
          },
        ],
      },
      columns: [
        {
          stat: "Count",
          type: "Aggregation",
          agg_field: "name",
          agg_relation: "patients.favbook",
        },
        {
          type: "Action",
          rndid: "1a8ac3",
          minRole: 10,
          isFormula: {},
          action_name: "run_js_code",
          action_size: "btn-sm",
          action_label: "you're my number",
          action_style: "btn-success",
          configuration: { code: 'console.log("1")' },
        },
      ],
      response: `<div class="row"><div class="col-sm-6 text-">1</div><div class="col-sm-6 text-"><a href="javascript:view_post('testshow', 'run_action', {rndid:'1a8ac3', id:1});" class="btn btn-success btn-sm">you're my number</a></div></div>`,
    });
    await test_show({
      layout: {
        widths: [6, 6],
        besides: [
          {
            above: [
              null,
              {
                type: "card",
                contents: {
                  type: "view_link",
                  view: "Own:authorshow",
                  minRole: 10,
                  in_modal: true,
                  view_label: "foo it",
                },
                isFormula: {},
              },
            ],
          },
          {
            type: "container",
            bgType: "Color",
            hAlign: "left",
            vAlign: "top",
            bgColor: "#a9a7a7",
            bgFileId: 1,
            contents: {
              url: "'https://countto.com/'+pages",
              text: "author",
              type: "link",
              isFormula: { url: true, text: true },
            },
            imageSize: "contain",
            minHeight: "100",
            textColor: "#ffffff",
            borderStyle: "solid",
            borderWidth: "1",
          },
        ],
      },
      columns: [
        {
          type: "ViewLink",
          view: "Own:authorshow",
          minRole: 10,
          in_modal: true,
        },
      ],
      response: `<div class="row"><div class="col-sm-6 text-"><div class="card shadow mt-4 " ><div class="card-body"><button class="btn btn-secondary btn-sm" onClick="ajax_modal('/view/authorshow?id=1')">foo it</button></div></div></div><div class="col-sm-6 text-"><div class="text-left" style="min-height: 100px; border: 1px solid black;  background-color: #a9a7a7; "><a href="https://countto.com/967"  >Herman Melville</a></div></div></div>`,
    });
    await test_show({
      layout: {
        type: "card",
        contents: {
          above: [
            { type: "blank", contents: "author", isFormula: { text: true } },
            { type: "line_break" },
            {
              name: "5da0c7",
              type: "view",
              view: "authorshow",
              state: "shared",
              contents: "Herman Melville",
            },
          ],
        },
        isFormula: {},
      },
      columns: [],
      response: `<div class="card shadow mt-4 " ><div class="card-body">author<br />Herman Melville</div></div>`,
    });
  });
});

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestWizardReportDynamic(common.TransactionCase):
    def setUp(self):
        super(TestWizardReportDynamic, self).setUp()
        # use the demodata.
        self.RD_template = self.env.ref("report_dynamic.demo_report_2")
        self.RD_report = self.env.ref("report_dynamic.demo_report_1")
        self.section1 = self.env.ref("report_dynamic.demo_section_1")
        self.section2 = self.env.ref("report_dynamic.demo_section_2")
        self.alias1 = self.env.ref("report_dynamic.demo_alias_1")
        self.alias2 = self.env.ref("report_dynamic.demo_alias_2")
        self.demouser = self.env.ref("base.user_demo")

    def test_action_generate_reports_form(self):
        wiz_model = self.env["wizard.report.dynamic"]
        #  Action should not exist.
        self.assertEquals(self.RD_report.window_action_exists, False)
        self.RD_report.create_action()
        self.RD_report._compute_window_action_exists()
        self.assertEquals(self.RD_report.window_action_exists, True)

        # TODO emulate form
        wiz = wiz_model.create({"template_id": self.RD_template.id})
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.demouser.partner_id.id],
        }
        action = wiz.with_context(ctx).action_generate_reports()
        report_id = action.get("domain")[0][2]
        report = self.env["report.dynamic"].browse(report_id)

        self.assertEquals(len(report), 1)
        self.assertEquals(report.res_id, self.demouser.partner_id.id)
        self.assertEquals(report.template_id, self.RD_template)

        # unlocked
        self.assertEquals(report.lock_date, False)
        # lock
        wiz_lock = self.env["wizard.lock.report"].create({"report_id": report.id})
        wiz_lock.action_lock_report()
        self.assertEquals(report.lock_date, fields.Date.today())
        # test inverse write on resource_ref
        res_partner_model = self.env.ref("base.model_res_partner")
        self.RD_report.write(
            {"resource_ref": "{},{}".format(res_partner_model.model, self.demouser.id)}
        )
        self.assertEquals(self.RD_report.res_id, self.RD_report.resource_ref.id)
        self.assertEquals(self.RD_report.model_id, res_partner_model)
        # final change model_id and t delete all records so  no sample record exists
        # (must be on template or will default to template.model_id
        new_model = self.env.ref("base.model_base_language_install")
        with self.assertRaises(UserError) as e:
            BLI_template = self.env["report.dynamic"].create(
                {
                    "name": "language template",
                    "resource_ref": self.env["base.language.install"]
                    .search([], limit=1)
                    .id,
                    "model_id": new_model.id,
                    "is_template": True,
                }
            )
            BLI_report = self.env["report.dynamic"].create(
                {
                    "name": "language template",
                    "resource_ref": self.env["base.language.install"]
                    .search([], limit=1)
                    .id,
                    "template_id": BLI_template.id,
                }
            )
            self.env["base.language.install"].search([]).unlink()
            BLI_report._compute_resource_ref()
        self.assertEqual(
            e.exception.name,
            "No sample record exists for Model base.language.install. "
            "Please create one before proceeding",
        )
        # testing the section methods
        content1 = self.section1._compute_dynamic_content()
        content2 = self.section2._compute_dynamic_content()
        self.assertEqual(content1, None)
        partner_startswith_d = self.env["res.partner"].create({"name": "Dperson"})
        self.RD_template.write(
            {
                "resource_ref": "{},{}".format(
                    res_partner_model.model, partner_startswith_d.id
                )
            }
        )
        self.RD_report.write(
            {
                "resource_ref": "{},{}".format(
                    res_partner_model.model, partner_startswith_d.id
                )
            }
        )
        content2 = self.section2._compute_dynamic_content()
        self.assertEqual(content2, None)

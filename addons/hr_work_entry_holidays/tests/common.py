from sigil.addons.hr_work_entry.tests.common import TestWorkEntryBase
from sigil.addons.hr_holidays.tests.common import TestHolidayContract

class TestWorkEntryHolidaysBase(TestWorkEntryBase, TestHolidayContract):

    @classmethod
    def setUpClass(cls):
        super(TestWorkEntryHolidaysBase, cls).setUpClass()
        cls.leave_type.work_entry_type_id = cls.work_entry_type_leave.id

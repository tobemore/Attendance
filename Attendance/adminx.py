import xadmin
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from xadmin.plugins.actions import BaseActionView
from xadmin.plugins.utils import get_context_dict
from xadmin.views import CommAdminView, BaseAdminPlugin

from Attendance.forms import DateSelectForm, ShiftsInfoDateForm
from Attendance.models import EmployeeInfo, OriginalCard, ShiftsInfo, EmployeeSchedulingInfo, EditAttendanceType, \
    EditAttendance, LeaveType, LeaveInfo, AttendanceExceptionStatus, AttendanceInfo, EmployeeInfoImport, \
    OriginalCardImport, LegalHoliday, AttendanceTotal
from Attendance.resources import EmployeeInfoResource, OriginalCardResource, EditAttendanceTypeResource, \
    LeaveTypeResource, EditAttendanceResource, LeaveInfoResource
from Attendance.views import get_path, loading_data, ShareContext, attendance_total_cal, form_select, attendance_cal, \
    shift_swap, cal_scheduling_info


class SelectedShiftsInfoAction(BaseActionView):
    # 这里需要填写三个属性
    #: 相当于这个 Action 的唯一标示, 尽量用比较针对性的名字
    action_name = "排班选择"
    #: 描述, 出现在 Action 菜单中, 可以使用 ``%(verbose_name_plural)s`` 代替 Model 的名字.
    description = '排班选择 %(verbose_name_plural)s'
    model_perm = 'change'  #: 该 Action 所需权限

    # 而后实现 do_action 方法
    # @filter_hook
    # 通过 ShareContext 实现所有的数据和模板与管理界面一致，同时访问链接 ^form_select ,将选择的数据回填到 callback 函数
    # argument_dict 这个字典里面的数据是 callback 参数
    def do_action(self, queryset):
        context = self.get_context()
        self.message_user("选择计算的开始日期和结束日期,以及班次(确保已完成法定节假日处理)")
        print(self.request.path)
        ShareContext(context=context, path=self.request.path, query_list=queryset, form=ShiftsInfoDateForm,
                     title='考勤计算', templates='Attendance/selected.html', callback=cal_scheduling_info,
                     argument_dict={one: "" for one in ShiftsInfoDateForm.base_fields})
        return redirect(form_select)


class ShiftSelectAction(BaseActionView):
    # 这里需要填写三个属性
    #: 相当于这个 Action 的唯一标示, 尽量用比较针对性的名字
    action_name = "调班"
    #: 描述, 出现在 Action 菜单中, 可以使用 ``%(verbose_name_plural)s`` 代替 Model 的名字.
    description = '调班 %(verbose_name_plural)s'
    model_perm = 'change'  #: 该 Action 所需权限

    # 而后实现 do_action 方法
    def do_action(self, queryset):
        context = self.get_context()
        self.message_user("选择要交换的日期")
        ShareContext(context=context, path=self.request.path, query_list=queryset, form=DateSelectForm, title='调班',
                     templates='Attendance/selected.html', callback=shift_swap,
                     argument_dict={one: "" for one in DateSelectForm.base_fields})
        return redirect(form_select)


class CalAttendanceAction(BaseActionView):
    # 这里需要填写三个属性
    #: 相当于这个 Action 的唯一标示, 尽量用比较针对性的名字
    action_name = "考勤计算"
    #: 描述, 出现在 Action 菜单中, 可以使用 ``%(verbose_name_plural)s`` 代替 Model 的名字.
    description = '考勤计算 %(verbose_name_plural)s'
    model_perm = 'change'  #: 该 Action 所需权限

    # 而后实现 do_action 方法
    def do_action(self, queryset):
        context = self.get_context()
        self.message_user("选择要计算考勤的日期")
        ShareContext(context=context, path=self.request.path, query_list=queryset, form=DateSelectForm, title='考勤计算',
                     templates='Attendance/selected.html', callback=attendance_cal,
                     argument_dict={one: "" for one in DateSelectForm.base_fields})
        return redirect(form_select)


class CalAttendanceTotalAction(BaseActionView):
    # 这里需要填写三个属性
    #: 相当于这个 Action 的唯一标示, 尽量用比较针对性的名字
    action_name = "考勤汇总"
    #: 描述, 出现在 Action 菜单中, 可以使用 ``%(verbose_name_plural)s`` 代替 Model 的名字.
    description = '考勤汇总 %(verbose_name_plural)s'
    model_perm = 'change'  #: 该 Action 所需权限

    # 而后实现 do_action 方法
    def do_action(self, queryset):
        context = self.get_context()
        self.message_user("选择要计算考勤汇总的日期")
        print({one: "" for one in DateSelectForm.base_fields})
        ShareContext(context=context, path=self.request.path, query_list=queryset, form=DateSelectForm, title='考勤汇总计算',
                     templates='Attendance/selected.html', callback=attendance_total_cal,
                     argument_dict={one: "" for one in DateSelectForm.base_fields})
        return redirect(form_select)


# 继承BaseAdminPlugin类
class ImportMenuPlugin(BaseAdminPlugin):
    # 使用插件时需要在ModelAdmin类中设置import_export_args属性，插件初始化时使用ModelAdmin的import_export_args进行赋值
    import_export_args = {}

    # 返回True则加载插件，在list列表中显示导入按钮
    def init_request(self, *args, **kwargs):
        return bool(self.import_export_args.get('import_resource_class'))

    def block_top_toolbar(self, context, nodes):
        has_change_perm = self.has_model_perm(self.model, 'change')
        has_add_perm = self.has_model_perm(self.model, 'add')
        if has_change_perm and has_add_perm:
            model_info = (self.opts.app_label, self.opts.model_name)
            import_url = reverse('xadmin:%s_%s_import' % model_info, current_app=self.admin_site.name)
            context = get_context_dict(context or {})  # no error!
            context.update({'import_url': import_url, })
            nodes.append(loader.render_to_string('xadmin/blocks/model_list.top_toolbar.importexport.import.html',
                                                 context=context))


@xadmin.sites.register(EmployeeInfo)
class EmployeeInfoAdmin(object):
    import_export_args = {'import_resource_class': EmployeeInfoResource, }
    list_display = ('code', 'name', 'level', 'emp_status', 'pwd_status')
    list_filter = ('level', 'emp_status',)
    search_fields = ('name', 'code',)
    actions = [SelectedShiftsInfoAction, ShiftSelectAction, CalAttendanceAction, CalAttendanceTotalAction, ]
    exclude = (
    'first_name', 'last_name', 'email', 'is_staff', 'date_joined', 'last_login', 'is_active', 'is_superuser', 'groups',
    'user_permissions')
    pass


@xadmin.sites.register(EmployeeInfoImport)
class EmployeeInfoImportAdmin(object):
    actions = ['upload_loading', ]

    def upload_loading(self, request, queryset):
        path = get_path(queryset)
        name_list = loading_data(path, EmployeeInfo)
        if len(name_list):
            self.message_user("{num}没有导入成功,{name}".format(num=len(name_list),
                                                          name='、'.join(sorted(set(name_list), key=name_list.index))))

    upload_loading.short_description = '解析文件'
    pass


@xadmin.sites.register(OriginalCard)
class OriginalCardAdmin(object):
    import_export_args = {'import_resource_class': OriginalCardResource, }
    model = OriginalCard
    list_display = ('emp', 'attendance_card',)
    # list_filter = ('level', 'emp_status', )
    search_fields = ('emp__code', 'emp__name',)
    date_hierarchy = 'attendance_card'

    pass


@xadmin.sites.register(OriginalCardImport)
class OriginalCardImportAdmin(object):
    actions = ['upload_loading', ]

    def upload_loading(self, request, queryset):
        path = get_path(queryset)
        name_list = loading_data(path, OriginalCard)
        if len(name_list):
            self.message_user("{num}没有导入成功,{name}".format(num=len(name_list),
                                                          name='、'.join(sorted(set(name_list), key=name_list.index))))

    upload_loading.short_description = '解析文件'
    pass


@xadmin.sites.register(ShiftsInfo)
class ShiftsInfoAdmin(object):
    list_display = ('name', 'type_shift', 'check_in', 'check_in_end', 'check_out_start', 'check_out', 'late_time',
                    'leave_early_time', 'absenteeism_time', 'status')
    pass


@xadmin.sites.register(LegalHoliday)
class LegalHolidayAdmin(object):
    list_display = ('legal_holiday_name', 'legal_holiday', 'status')
    list_filter = ('status',)
    ordering = ('legal_holiday',)
    pass


@xadmin.sites.register(EmployeeSchedulingInfo)
class EmployeeSchedulingInfoAdmin(object):
    # actions = [SelectedShiftsInfoAction, ShiftSelectAction, ]
    list_display = ('emp', 'attendance_date', 'shifts_verbose_name')
    list_filter = ('attendance_date', 'emp__level')
    search_fields = ('emp__code', 'emp__name')
    ordering = ('emp', 'attendance_date')
    pass


@xadmin.sites.register(EditAttendanceType)
class EditAttendanceTypeAdmin(object):
    import_export_args = {'import_resource_class': EditAttendanceTypeResource, }
    pass


@xadmin.sites.register(EditAttendance)
class EditAttendanceAdmin(object):
    # actions = []
    import_export_args = {'import_resource_class': EditAttendanceResource, }
    list_display = (
        'emp', 'edit_attendance_date', 'edit_attendance_time_start', 'edit_attendance_time_end', 'edit_attendance_type',
        'edit_attendance_status')
    list_filter = ('edit_attendance_type',)
    search_fields = ('emp__code', 'emp__name')

    pass


@xadmin.sites.register(LeaveType)
class LeaveTypeAdmin(object):
    import_export_args = {'import_resource_class': LeaveTypeResource, }
    pass


@xadmin.sites.register(LeaveInfo)
class LeaveInfoAdmin(object):
    import_export_args = {'import_resource_class': LeaveInfoResource, }
    list_display = (
    'emp', 'start_date', 'leave_info_time_start', 'end_date', 'leave_info_time_end', 'leave_type', 'leave_info_status',)
    list_filter = ('leave_type',)
    search_fields = ('emp__code', 'emp__name')
    pass


@xadmin.sites.register(AttendanceExceptionStatus)
class AttendanceExceptionStatusAdmin(object):
    pass


@xadmin.sites.register(AttendanceInfo)
class AttendanceInfoAdmin(object):
    list_display = (
        'emp', 'attendance_date', 'check_in', 'check_in_type', 'check_in_status', 'check_out', 'check_out_type',
        'check_out_status', 'check_status')
    list_filter = (
        'attendance_date', 'check_in_status', 'check_out_status', 'check_status', 'emp__level', 'emp__emp_status',
        'attendance_date_status')
    search_fields = ('emp__code', 'emp__name')
    ordering = ('emp', 'attendance_date')

    pass


@xadmin.sites.register(AttendanceTotal)
class AttendanceTotalAdmin(object):
    list_display = (
        'emp_code', 'emp_name', 'section_date', 'arrive_total', 'real_arrive_total', 'absenteeism_total', 'late_total',
        'sick_leave_total', 'personal_leave_total', 'annual_leave_total', 'marriage_leave_total',
        'bereavement_leave_total', 'paternity_leave_total', 'maternity_leave_total', 'work_related_injury_leave_total',
        'home_leave_total', 'travelling_total', 'other_leave_total',)
    list_filter = ('emp_name__level', 'emp_name__emp_status', 'section_date',)
    search_fields = ('emp_name__code', 'emp_name__name')
    ordering = ('emp_code', 'section_date')

    pass


class GlobalSetting(object):
    # 设置base_site.html的Title
    site_title = '考勤信息处理'
    # 设置base_site.html的Footer
    site_footer = '考勤信息处理平台'


xadmin.site.register(CommAdminView, GlobalSetting)

# xadmin.site.register(EmployeeInfo)
# xadmin.site.register(OriginalCard)
# xadmin.site.register(ShiftsInfo)
# xadmin.site.register(EmployeeSchedulingInfo)
# xadmin.site.register(EditAttendanceType)
# xadmin.site.register(EditAttendance)
# xadmin.site.register(LeaveType)
# xadmin.site.register(LeaveInfo)
# xadmin.site.register(AttendanceExceptionStatus)
# xadmin.site.register(AttendanceInfo)
-- This SQL script creates a table named `person_context` in the `test` dataset.
-- It joins two tables: `email_deptm_lookup` and `deptm_context_regionarea` based on specific columns.

Create or replace table test.person_context as (
  select a.EmployeeCorporateEmail as employee_corporate_email,
         a.Area as area,
         a.Region as region,
         a.OpsOrSupport as ops_or_support,
         b.AreaCount as area_count,
         b.Context as department_context
   from `test.email_deptm_lookup` as a
  left join `test.deptm_context_regionarea` as b
  on a.Area = b.Area and 
  a.Region = b.Region and
  a.OpsOrSupport = b.OpsOrSupport
)


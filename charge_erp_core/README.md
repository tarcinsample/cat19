# Charge ERP Core

This is the core module for the Charge ERP School Management System.

## Features

*   **Student Management:** Manage student records, including personal and contact information.
*   **Faculty Management:** Manage faculty records, including personal and contact information.
*   **Course Management:** Define courses and their evaluation methods.
*   **Subject Management:** Define subjects, their types, and grade weightings.
*   **Batch Management:** Create and manage batches for courses.
*   **Program Management:** Define academic programs and their levels.
*   **Department Management:** Manage academic departments.
*   **Academic Year Management:** Define academic years and their corresponding terms.

## Models

This module includes the following models:

*   `op.student`
*   `op.course`
*   `op.faculty`
*   `op.subject`
*   `op.batch`
*   `op.program`
*   `op.program.level`
*   `op.department`
*   `op.academic.year`
*   `op.academic.term`

## Deployment

To deploy this module, follow these steps:

1.  Add the `charge_erp_core` directory to your Odoo addons path.
2.  Restart the Odoo server.
3.  Go to **Apps** in the Odoo backend.
4.  Click **Update Apps List**.
5.  Search for "Charge ERP Core" and click **Install**.

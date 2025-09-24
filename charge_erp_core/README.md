# Charge ERP Core Module

This module contains the core models and functionality for the Charge ERP system.

## Features

As of the current version, this module includes the following features:
- A `School` menu in the Odoo interface.
- Basic models for managing:
    - Students (`op.student`)
    - Courses (`op.course`)
    - Faculties (`op.faculty`)
    - Subjects (`op.subject`)
    - Batches (`op.batch`)
    - Program Levels (`op.program.level`)
    - Programs (`op.program`)
    - Departments (`op.department`)
    - Academic Terms (`op.academic.term`)
    - Academic Years (`op.academic.year`)
- Basic views (list and form) and menu items for each of the above models.
- Basic access rights for all new models.

## How to Deploy

To deploy this module, please follow these steps:

1.  **Ensure you have a running Odoo 19 instance.**
2.  **Add this module to your addons path.** Place the `charge_erp_core` directory into the `addons` directory of your Odoo installation.
3.  **Restart your Odoo server.** This is necessary for Odoo to recognize the new module.
4.  **Activate Developer Mode.** In your Odoo instance, go to `Settings` -> `General Settings` and click on `Activate the developer mode`.
5.  **Update the Apps List.** Go to `Apps` in the main menu and click on `Update Apps List` in the secondary menu. You will be prompted to confirm the update.
6.  **Install the Module.** Search for `Charge ERP Core` in the Apps list (you may need to remove the default "Apps" filter to see it). Click the "Install" button on the module.

Once the installation is complete, you will see a new "School" menu in your Odoo instance where you can manage the new models.

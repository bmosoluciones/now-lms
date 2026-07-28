# Intent Solutions Learn — live login / roles / admin flow

The documented, **verified** authentication and administration flow for
`learn.intentsolutions.io` (our NOW-LMS fork). The onboarding lessons in
`cca/lessons/getting-started/` are written from this file. Routes are
from the fork source (`now_lms/vistas/`); config values are read from the live
database.

> **Verified 2026-07-21 against the running `now-lms-app-1` container.** Re-read
> the live `Configuracion` before treating the config-dependent notes below as
> current — an admin can change them at any time.

## Live configuration (as observed)

| Setting | Live value | Effect |
|---|---|---|
| Site title | `Intent Solutions Learn` | — |
| `verify_user_by_email` | **off** | No confirmation email is sent on registration |
| `allow_unverified_email_login` | **off** | Unverified users are **not** auto-activated at login |
| Mail server (`MailConfig.MAIL_SERVER`) | **not configured** | Confirmation + password-reset emails cannot send; the "Forgot password?" link is hidden |

**Consequence of the current config:** a self-registered student is created
**inactive** and there is no email path to self-activate, so **new sign-ups
require an admin to activate them** (or an admin must first configure mail +
enable `verify_user_by_email`, or enable `allow_unverified_email_login`). This is
the single most important operational fact for onboarding today.

## Roles (`Usuario.tipo`, `now_lms/db/__init__.py`)

Four roles, plus two status flags:

- **admin** — full access; bypasses every `perfil_requerido` gate.
- **instructor** — creates/manages courses, sections, evaluations, questions.
- **moderator** — moderation surfaces (forum, flagged messages, blog).
- **student** — enrolls in and takes courses. *(The model comment lists "user";
  the code actually stores `tipo="student"` — both self-registration and the
  admin "new user" form write `"student"`, and the dashboard dispatches on
  `"student"`.)*
- `activo` (Boolean) — active/inactive. Inactive accounts cannot log in.
- `correo_electronico_verificado` (Boolean) — email-verified flag.

Access is gated by `perfil_requerido(<role or tuple>)` + `login_required`
(`now_lms/auth.py`); admin always passes.

## Student flow

| Step | Route (endpoint) | Notes |
|---|---|---|
| Register | `GET/POST /user/logon` (`user.crear_cuenta`) | Form: name, last name, email (used as username), password. Creates `tipo="student"`, `activo=False`. |
| Email verify *(only if `verify_user_by_email` on)* | `GET /user/check_mail/<token>` | Sets `correo_electronico_verificado=True` **and** `activo=True`. Requires mail configured. |
| Log in | `GET/POST /user/login` (`user.inicio_sesion`) | Accepts username **or** email + password. **Blocks inactive accounts** ("Su cuenta está inactiva") unless `allow_unverified_email_login` is on. |
| Dashboard | `GET /home/panel` (`home.panel`) | Role-dispatched; students see their enrolled courses + certificates. |
| Enroll | course pages under `/course/…` | See `enrolling-and-progress` lesson. |
| Password reset | `GET/POST /user/forgot_password` → emailed token → `GET/POST /user/reset_password/<token>` | The "Forgot password?" link only appears when mail is configured — **currently hidden**. |

## Admin / instructor flow

| Step | Route (endpoint) | Notes |
|---|---|---|
| Log in | `GET/POST /user/login` | Same login; role gates what's reachable next. |
| Admin panel | `GET /admin/panel` (`admin_profile`) | Admin cockpit. (Admins also get an admin view at `/home/panel`.) |
| List users | `GET /admin/users/list` | All users. |
| Inactive / unverified | `GET /admin/users/list_inactive`, `GET /admin/users/list_unverified` | Where new sign-ups land under the current config. |
| Activate / deactivate | `POST /admin/users/set_active/<user_id>`, `POST /admin/users/set_inactive/<user_id>` | **Activation is how a new student gets in today.** |
| Verify email manually | `POST /admin/users/verify_email/<user_id>` | Manual override when mail is off. |
| Delete user | `POST /admin/users/delete/<user_id>` | — |
| Create a staff user | `GET/POST /user/new_user` (`user.crear_usuario`, admin-only) | Creates `activo=True`, `correo_electronico_verificado=True`, `tipo="student"`; elevate the role afterward from the user's admin profile page (`/user/<username>`). |
| Instructor panel | `GET /instructor` and `/instructor/…` | Course, section, evaluation, and question management. |

## Site configuration & mail (admin)

- General settings: `GET/POST /setting/general`.
- Mail: `GET/POST /setting/mail`, verify with `GET/POST /setting/mail/verify`.
- Official NOW-LMS references:
  `bmosoluciones.github.io/now-lms/{configure,mail,setup,setup-conf}/`.

## Future decision — Google sign-in

Google (OAuth) sign-in is **not built** in this fork today; sign-in is
username/email + password only. Note it as a future decision — do not document a
Google button that does not exist. Confirm against the live config before writing
any lesson that mentions it.

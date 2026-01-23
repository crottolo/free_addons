"""REST API endpoint for server info monitoring.

Provides a public API endpoint to retrieve Odoo server version,
addons paths, and module information.

Endpoint: GET /api/server/info
Authentication: Bearer token (configured in System Parameters)

Multi-database support:
    - Query param: ?db=database_name
    - Header: X-Odoo-Database: database_name
"""

import logging

import odoo.modules.registry
import odoo.service.common
import odoo.service.db
from odoo import SUPERUSER_ID, api, fields, http
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)


class ServerInfoController(http.Controller):
    """API Controller for Server Info Monitor."""

    _api_url = "/api/server/info"
    _config_token_key = "server_info_monitor.token"

    # ============================================
    # HELPER METHODS
    # ============================================

    def _get_database(self, kwargs):
        """Get database name from request params, header, or default.

        Priority:
            1. Query param: ?db=database_name
            2. Header: X-Odoo-Database
            3. Default from request.db or config

        Returns:
            str: Database name or None if not found.
        """
        # From query param
        db = kwargs.get("db")
        if db:
            return db

        # From header
        db = request.httprequest.headers.get("X-Odoo-Database")
        if db:
            return db

        # From request (if already set by Odoo)
        if hasattr(request, "db") and request.db:
            return request.db

        # From config db_name
        if config.get("db_name"):
            db_list = config.get("db_name").split(",")
            if db_list:
                return db_list[0].strip()

        return None

    def _validate_database(self, db):
        """Check if database exists and is accessible.

        Args:
            db: Database name to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not db:
            return False
        try:
            db_list = odoo.service.db.list_dbs(True)
            return db in db_list
        except Exception:
            return False

    def _validate_token_for_db(self, env):
        """Validate Bearer token from Authorization header.

        Args:
            env: Odoo environment for the target database.

        Returns:
            bool: True if token is valid, False otherwise.
        """
        expected_token = (
            env["ir.config_parameter"].sudo().get_param(self._config_token_key)
        )
        if not expected_token:
            _logger.warning("Server Info Monitor: Token not configured")
            return False

        auth_header = request.httprequest.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False

        provided_token = auth_header[7:]  # Remove "Bearer " prefix
        return provided_token == expected_token

    def _error_response(self, message, status=400):
        """Create standardized error response.

        Args:
            message: Error message string.
            status: HTTP status code.

        Returns:
            JSON response with error details.
        """
        return request.make_json_response(
            {
                "success": False,
                "error": message,
                "timestamp": fields.Datetime.now().isoformat(),
            },
            status=status,
        )

    def _format_module_data(self, module, include_state=True):
        """Format module record for JSON response.

        Args:
            module: ir.module.module record.
            include_state: Whether to include state field.

        Returns:
            dict: Formatted module data.
        """
        data = {
            "name": module.name,
            "version": module.installed_version or module.latest_version or "",
            "author": module.author or "",
            "application": module.application,
        }
        if include_state:
            data["state"] = module.state
        return data

    def _get_user_stats(self, cr):
        """Get user statistics.

        Args:
            cr: Database cursor.

        Returns:
            dict: User statistics including total internal users and active users.
        """

        # Get internal users with last login
        cr.execute("""
            SELECT
                u.id,
                u.login,
                p.name,
                MAX(l.create_date) as last_activity
            FROM res_users u
            JOIN res_partner p ON u.partner_id = p.id
            LEFT JOIN res_users_log l ON l.create_uid = u.id
            WHERE u.active = true AND u.share = false
            GROUP BY u.id, u.login, p.name
            ORDER BY last_activity DESC NULLS LAST
        """)
        users_data = cr.fetchall()

        # Count users logged in last 30 days
        cr.execute("""
            SELECT COUNT(DISTINCT l.create_uid)
            FROM res_users_log l
            JOIN res_users u ON l.create_uid = u.id
            WHERE u.active = true AND u.share = false
              AND l.create_date >= CURRENT_DATE - INTERVAL '30 days'
        """)
        active_last_30_days = cr.fetchone()[0]

        # Count portal users (share=true, active=true)
        cr.execute("""
            SELECT COUNT(*)
            FROM res_users
            WHERE active = true AND share = true
        """)
        total_portal = cr.fetchone()[0]

        # Count inactive users (active=false)
        cr.execute("""
            SELECT COUNT(*)
            FROM res_users
            WHERE active = false
        """)
        total_inactive = cr.fetchone()[0]

        # Format user list
        user_list = [
            {
                "id": row[0],
                "login": row[1],
                "name": row[2],
                "last_activity": row[3].isoformat() if row[3] else None,
            }
            for row in users_data
        ]

        return {
            "total_internal": len(users_data),
            "active_last_30_days": active_last_30_days,
            "total_portal": total_portal,
            "total_inactive": total_inactive,
            "list": user_list,
        }

    def _get_license_info(self, env, version_info):
        """Get license and enterprise information.

        Args:
            env: Odoo environment.
            version_info: Server version info dict.

        Returns:
            dict: License information.
        """
        ICP = env["ir.config_parameter"].sudo()

        # Check if Enterprise (version_info contains "e")
        server_version_info = version_info.get("server_version_info", [])
        is_enterprise = "e" in server_version_info if server_version_info else False

        # Get license parameters
        expiration_date = ICP.get_param("database.expiration_date", "")
        enterprise_code = ICP.get_param("database.enterprise_code", "")
        expiration_reason = ICP.get_param("database.expiration_reason", "")
        is_neutralized = ICP.get_param("database.is_neutralized", "false")

        return {
            "is_enterprise": is_enterprise,
            "expiration_date": expiration_date or None,
            "enterprise_code": enterprise_code or None,
            "expiration_reason": expiration_reason or None,
            "is_neutralized": is_neutralized.lower() == "true"
            if isinstance(is_neutralized, str)
            else bool(is_neutralized),
        }

    # ============================================
    # API ENDPOINT
    # ============================================

    @http.route(
        _api_url,
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def get_server_info(self, **kwargs):
        """Get server information and module list.

        Query Parameters:
            db (str): Database name (optional, for multi-database instances).
            refresh (str): If "true", refresh module list before returning.

        Headers:
            X-Odoo-Database: Database name (alternative to ?db= param).
            Authorization: Bearer token.

        Returns:
            JSON response with server info, addons paths, and modules.
        """
        try:
            # Determine which database to use
            db = self._get_database(kwargs)
            if not db:
                return self._error_response(
                    "Database not specified. Use ?db=name or X-Odoo-Database header.",
                    400,
                )

            # Validate database exists
            if not self._validate_database(db):
                return self._error_response(f"Database '{db}' not found.", 404)

            # Get registry and create environment for the database
            registry = odoo.modules.registry.Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})

                # Validate token for this database
                if not self._validate_token_for_db(env):
                    return self._error_response(
                        "Unauthorized: Invalid or missing token",
                        401,
                    )

                Module = env["ir.module.module"].sudo()

                # Refresh module list if requested
                refresh = kwargs.get("refresh", "").lower() == "true"
                if refresh:
                    _logger.info(
                        "Server Info Monitor: Refreshing module list for %s",
                        db,
                    )
                    Module.update_list()

                # Get server version info
                version_info = odoo.service.common.exp_version()

                # Get addons paths
                addons_paths = config.get("addons_path", "").split(",")
                addons_paths = [p.strip() for p in addons_paths if p.strip()]

                # Get user statistics
                user_stats = self._get_user_stats(cr)

                # Get license info
                license_info = self._get_license_info(env, version_info)

                # Get all available modules
                all_modules = Module.search([], order="name")

                # Get installed modules
                installed_modules = Module.search(
                    [("state", "=", "installed")],
                    order="name",
                )

                # Count modules to upgrade
                to_upgrade_count = Module.search_count([("state", "=", "to upgrade")])

                # Format response
                response_data = {
                    "success": True,
                    "timestamp": fields.Datetime.now().isoformat(),
                    "database": db,
                    "server": {
                        "version": version_info.get("server_version", ""),
                        "version_info": version_info.get("server_version_info", []),
                        "serie": version_info.get("server_serie", ""),
                    },
                    "license": license_info,
                    "users": user_stats,
                    "addons_paths": addons_paths,
                    "modules": {
                        "available": {
                            "total": len(all_modules),
                            "list": [
                                self._format_module_data(m, include_state=True)
                                for m in all_modules
                            ],
                        },
                        "installed": {
                            "total": len(installed_modules),
                            "to_upgrade": to_upgrade_count,
                            "list": [
                                self._format_module_data(m, include_state=False)
                                for m in installed_modules
                            ],
                        },
                    },
                }

                return request.make_json_response(response_data, status=200)

        except Exception as e:
            _logger.exception("Server Info Monitor: Error getting server info")
            return self._error_response(f"Internal server error: {e!s}", 500)

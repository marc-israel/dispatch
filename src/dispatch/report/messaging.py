import logging

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from dispatch.conversation.enums import ConversationCommands
from dispatch.database.core import resolve_attr
from dispatch.incident import service as incident_service
from dispatch.incident.models import Incident
from dispatch.messaging.strings import (
    INCIDENT_EXECUTIVE_REPORT,
    INCIDENT_REPORT_REMINDER,
    INCIDENT_REPORT_REMINDER_DELAYED,
    INCIDENT_TACTICAL_REPORT,
    MessageType,
)
from dispatch.plugin import service as plugin_service

from .enums import ReportTypes
from .models import Report

log = logging.getLogger(__name__)


def get_report_reminder_settings(report_type: ReportTypes):
    report_reminder_settings_map = {
        ReportTypes.tactical_report: (
            ConversationCommands.tactical_report,
            MessageType.incident_tactical_report,
        ),
        ReportTypes.executive_report: (
            ConversationCommands.executive_report,
            MessageType.incident_executive_report,
        ),
    }

    return report_reminder_settings_map.get(report_type, (None, None))


def send_tactical_report_to_conversation(
    incident_id: int, conditions: str, actions: str, needs: str, db_session: Session
):
    """Sends a tactical report to the conversation."""
    # we load the incident instance
    incident = incident_service.get(db_session=db_session, incident_id=incident_id)

    plugin = plugin_service.get_active_instance(
        db_session=db_session, project_id=incident.project.id, plugin_type="conversation"
    )

    if not plugin:
        log.warning("Tactical report not sent, no conversation plugin enabled.")
        return

    plugin.instance.send(
        incident.conversation.channel_id,
        "Incident Tactical Report",
        INCIDENT_TACTICAL_REPORT,
        notification_type=MessageType.incident_tactical_report,
        persist=True,
        conditions=conditions,
        actions=actions,
        needs=needs,
    )

    log.debug("Tactical report sent to conversation {incident.conversation.channel_id}.")


def send_tactical_report_to_tactical_group(
    incident_id: int,
    tactical_report: Report,
    db_session: Session,
):
    """Sends a tactical report to the tactical group."""
    # we load the incident instance
    incident = incident_service.get(db_session=db_session, incident_id=incident_id)

    plugin = plugin_service.get_active_instance(
        db_session=db_session, project_id=incident.project.id, plugin_type="email"
    )

    if not plugin:
        log.warning("Tactical report not sent. No email plugin enabled.")
        return

    notification_text = "Tactical Report"

    # Can raise exception "tenacity.RetryError: RetryError". (Email may still go through).
    try:
        plugin.instance.send(
            incident.tactical_group.email,
            notification_text,
            INCIDENT_TACTICAL_REPORT,
            MessageType.incident_tactical_report,
            name=incident.name,
            title=incident.title,
            conditions=tactical_report.details.get("conditions"),
            actions=tactical_report.details.get("actions"),
            needs=tactical_report.details.get("needs"),
            contact_fullname=incident.commander.individual.name,
            contact_team=incident.commander.team,
            contact_weblink=incident.commander.individual.weblink,
        )
    except Exception as e:
        log.error(
            f"Error in sending {notification_text} email to {incident.tactical_group.email}: {e}"
        )

    log.debug(f"Tactical report sent to tactical group {incident.tactical_group.email}.")


def send_executive_report_to_notifications_group(
    incident_id: int,
    executive_report: Report,
    db_session: Session,
):
    """Sends an executive report to the notifications group."""
    # we load the incident instance
    incident = incident_service.get(db_session=db_session, incident_id=incident_id)

    plugin = plugin_service.get_active_instance(
        db_session=db_session, project_id=incident.project.id, plugin_type="email"
    )

    if not plugin:
        log.warning("Executive report not sent. No email plugin enabled.")
        return

    notification_text = "Executive Report"
    plugin.instance.send(
        incident.notifications_group.email,
        notification_text,
        INCIDENT_EXECUTIVE_REPORT,
        MessageType.incident_executive_report,
        name=incident.name,
        title=incident.title,
        current_status=executive_report.details.get("current_status"),
        overview=executive_report.details.get("overview"),
        next_steps=executive_report.details.get("next_steps"),
        weblink=executive_report.document.weblink,
        notifications_group=incident.notifications_group.email,
        contact_fullname=incident.commander.individual.name,
        contact_weblink=incident.commander.individual.weblink,
    )

    log.debug(f"Executive report sent to notifications group {incident.notifications_group.email}.")


def send_incident_report_reminder(
    incident: Incident, report_type: ReportTypes, db_session: Session, reminder=False
):
    """Sends a direct message to the incident commander indicating that they should complete a report."""
    message_text = f"Incident {report_type} Reminder"
    message_template = INCIDENT_REPORT_REMINDER_DELAYED if reminder else INCIDENT_REPORT_REMINDER
    command_name, message_type = get_report_reminder_settings(report_type)

    # Null out db attribute if this is a delayed reminder
    if reminder:
        if report_type == ReportTypes.tactical_report:
            incident.delay_tactical_report_reminder = None
        elif report_type == ReportTypes.executive_report:
            incident.delay_executive_report_reminder = None
        db_session.add(incident)
        db_session.commit()

    # check to see if there wasn't a recent report
    now = datetime.utcnow()
    if incident.last_tactical_report:
        last_reported_at = incident.last_tactical_report.created_at
        if now - last_reported_at < timedelta(hours=1):
            return

    plugin = plugin_service.get_active_instance(
        db_session=db_session, project_id=incident.project.id, plugin_type="conversation"
    )
    if not plugin:
        log.warning("Incident report reminder not sent, no conversation plugin enabled.")
        return

    report_command = plugin.instance.get_command_name(command_name)
    ticket_weblink = resolve_attr(incident, "ticket.weblink")

    items = [
        {
            "command": report_command,
            "name": incident.name,
            "report_type": report_type,
            "ticket_weblink": ticket_weblink,
            "title": incident.title,
            "incident_id": incident.id,
            "organization_slug": incident.project.organization.slug,
        }
    ]

    plugin.instance.send_direct(
        incident.commander.individual.email,
        message_text,
        message_template,
        message_type,
        items=items,
    )
    log.debug(f"Incident report reminder sent to {incident.commander.individual.email}.")

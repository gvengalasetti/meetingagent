#!/usr/bin/env python3
"""
Enhanced Chrome Extension Server with Calendar Person Research Agent Integration
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import traceback
import sys
import os

# Add the agents directory to the path
sys.path.append('/home/guna/Interview')
from agents.calendar_person_research_agent import CalendarPersonResearchAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# Initialize the enhanced calendar agent
try:
    calendar_agent = CalendarPersonResearchAgent()
    print("✅ Enhanced Calendar Person Research Agent initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing enhanced calendar agent: {e}")
    calendar_agent = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent_available': calendar_agent is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/meetings/<date_str>', methods=['GET'])
def get_meetings_for_date(date_str):
    """Get meetings for a specific date with attendee research"""
    
    if not calendar_agent:
        return jsonify({
            'error': 'Calendar agent not available',
            'meetings': []
        }), 500
    
    try:
        # Parse the date
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Search for meetings on this date using multiple strategies
        meetings = []
        
        # Strategy 1: Search by date string
        meetings = calendar_agent.search_meetings_by_keyword(date_str, max_results=10)
        
        # Strategy 2: If no meetings found, try different date formats
        if not meetings:
            date_formats = [
                target_date.strftime('%B %d, %Y'),  # "September 24, 2025"
                target_date.strftime('%b %d, %Y'),  # "Sep 24, 2025"
                target_date.strftime('%m/%d/%Y'),   # "09/24/2025"
                target_date.strftime('%m/%d'),      # "09/24"
                str(target_date.day),               # "24"
                target_date.strftime('%Y-%m-%d'),   # "2025-09-24"
            ]
            
            for date_format in date_formats:
                meetings = calendar_agent.search_meetings_by_keyword(date_format, max_results=10)
                if meetings:
                    break
        
        # Strategy 3: If still no meetings, get all meetings and filter by date
        if not meetings:
            try:
                # Get all meetings with various keywords and filter by date
                all_meetings = []
                keywords = ['meeting', 'interview', 'call', 'appointment', 'session', 'discussion', 'event']
                
                for keyword in keywords:
                    keyword_meetings = calendar_agent.search_meetings_by_keyword(keyword, max_results=20)
                    all_meetings.extend(keyword_meetings)
                
                # Remove duplicates
                unique_meetings = []
                seen_titles = set()
                for meeting in all_meetings:
                    if meeting.meeting_title not in seen_titles:
                        unique_meetings.append(meeting)
                        seen_titles.add(meeting.meeting_title)
                
                # Filter by date
                filtered_meetings = []
                for meeting in unique_meetings:
                    if meeting.start_time:
                        meeting_date = meeting.start_time.date()
                        if meeting_date == target_date.date():
                            filtered_meetings.append(meeting)
                
                meetings = filtered_meetings
                print(f"Found {len(meetings)} meetings for {date_str} after filtering")
            except Exception as e:
                print(f"Error in date filtering: {e}")
        
        # Process meetings and add research data
        enhanced_meetings = []
        for meeting in meetings:
            # Research attendees for this meeting
            research_results = calendar_agent.research_meeting_attendees(meeting)
            
            # Create enhanced meeting object
            enhanced_meeting = {
                'id': meeting.meeting_id,
                'title': meeting.meeting_title,
                'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
                'end_time': meeting.end_time.isoformat() if meeting.end_time else None,
                'location': meeting.location,
                'description': meeting.description,
                'attendees': [],
                'research_summary': '',
                'preparation_questions': ''
            }
            
            # Add attendee information with research
            for result in research_results:
                attendee_info = {
                    'name': result.attendee.display_name,
                    'email': result.attendee.email,
                    'company': result.attendee.company,
                    'title': result.attendee.title,
                    'research_summary': result.research_summary,
                    'found_info': result.found_info
                }
                enhanced_meeting['attendees'].append(attendee_info)
            
            # Generate meeting summary and questions
            try:
                meeting_summary = calendar_agent.generate_meeting_summary(meeting, research_results)
                preparation_questions = calendar_agent.generate_meeting_type_questions(meeting, research_results)
                
                enhanced_meeting['research_summary'] = meeting_summary
                enhanced_meeting['preparation_questions'] = preparation_questions
            except Exception as e:
                print(f"Error generating summary for meeting {meeting.meeting_title}: {e}")
                enhanced_meeting['research_summary'] = "Error generating research summary"
                enhanced_meeting['preparation_questions'] = "Error generating preparation questions"
            
            enhanced_meetings.append(enhanced_meeting)
        
        return jsonify({
            'date': date_str,
            'meetings': enhanced_meetings,
            'count': len(enhanced_meetings)
        })
        
    except Exception as e:
        print(f"Error processing date {date_str}: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'meetings': []
        }), 500

@app.route('/meeting/<meeting_id>', methods=['GET'])
def get_meeting_details(meeting_id):
    """Get detailed information for a specific meeting"""
    
    if not calendar_agent:
        return jsonify({
            'error': 'Calendar agent not available'
        }), 500
    
    try:
        # Get meeting by ID
        meeting = calendar_agent.get_meeting_by_id(meeting_id)
        
        if not meeting:
            return jsonify({
                'error': 'Meeting not found'
            }), 404
        
        # Research attendees
        research_results = calendar_agent.research_meeting_attendees(meeting)
        
        # Generate comprehensive analysis
        meeting_summary = calendar_agent.generate_meeting_summary(meeting, research_results)
        preparation_questions = calendar_agent.generate_meeting_type_questions(meeting, research_results)
        
        # Create detailed response
        meeting_details = {
            'id': meeting.meeting_id,
            'title': meeting.meeting_title,
            'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
            'end_time': meeting.end_time.isoformat() if meeting.end_time else None,
            'location': meeting.location,
            'description': meeting.description,
            'attendees': [],
            'research_summary': meeting_summary,
            'preparation_questions': preparation_questions
        }
        
        # Add attendee information
        for result in research_results:
            attendee_info = {
                'name': result.attendee.display_name,
                'email': result.attendee.email,
                'company': result.attendee.company,
                'title': result.attendee.title,
                'research_summary': result.research_summary,
                'found_info': result.found_info
            }
            meeting_details['attendees'].append(attendee_info)
        
        return jsonify(meeting_details)
        
    except Exception as e:
        print(f"Error getting meeting details for {meeting_id}: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/next-meeting', methods=['GET'])
def get_next_meeting():
    """Get the next upcoming meeting with research"""
    
    if not calendar_agent:
        return jsonify({
            'error': 'Calendar agent not available'
        }), 500
    
    try:
        # Get next meeting
        meeting = calendar_agent.get_next_meeting_info()
        
        if not meeting:
            return jsonify({
                'message': 'No upcoming meetings found',
                'meeting': None
            })
        
        # Research attendees
        research_results = calendar_agent.research_meeting_attendees(meeting)
        
        # Generate analysis
        meeting_summary = calendar_agent.generate_meeting_summary(meeting, research_results)
        preparation_questions = calendar_agent.generate_meeting_type_questions(meeting, research_results)
        
        # Create response
        meeting_data = {
            'id': meeting.meeting_id,
            'title': meeting.meeting_title,
            'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
            'end_time': meeting.end_time.isoformat() if meeting.end_time else None,
            'location': meeting.location,
            'description': meeting.description,
            'attendees': [],
            'research_summary': meeting_summary,
            'preparation_questions': preparation_questions
        }
        
        # Add attendee information
        for result in research_results:
            attendee_info = {
                'name': result.attendee.display_name,
                'email': result.attendee.email,
                'company': result.attendee.company,
                'title': result.attendee.title,
                'research_summary': result.research_summary,
                'found_info': result.found_info
            }
            meeting_data['attendees'].append(attendee_info)
        
        return jsonify({
            'meeting': meeting_data
        })
        
    except Exception as e:
        print(f"Error getting next meeting: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/search-meetings', methods=['POST'])
def search_meetings():
    """Search for meetings by keyword"""
    
    if not calendar_agent:
        return jsonify({
            'error': 'Calendar agent not available'
        }), 500
    
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        
        if not keyword:
            return jsonify({
                'error': 'Keyword is required'
            }), 400
        
        # Search for meetings
        meetings = calendar_agent.search_meetings_by_keyword(keyword, max_results=5)
        
        # Process meetings
        enhanced_meetings = []
        for meeting in meetings:
            research_results = calendar_agent.research_meeting_attendees(meeting)
            
            meeting_data = {
                'id': meeting.meeting_id,
                'title': meeting.meeting_title,
                'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
                'end_time': meeting.end_time.isoformat() if meeting.end_time else None,
                'location': meeting.location,
                'description': meeting.description,
                'attendees': [],
                'research_summary': '',
                'preparation_questions': ''
            }
            
            # Add attendee information
            for result in research_results:
                attendee_info = {
                    'name': result.attendee.display_name,
                    'email': result.attendee.email,
                    'company': result.attendee.company,
                    'title': result.attendee.title,
                    'research_summary': result.research_summary,
                    'found_info': result.found_info
                }
                meeting_data['attendees'].append(attendee_info)
            
            # Generate analysis
            try:
                meeting_summary = calendar_agent.generate_meeting_summary(meeting, research_results)
                preparation_questions = calendar_agent.generate_meeting_type_questions(meeting, research_results)
                
                meeting_data['research_summary'] = meeting_summary
                meeting_data['preparation_questions'] = preparation_questions
            except Exception as e:
                print(f"Error generating analysis for meeting {meeting.meeting_title}: {e}")
                meeting_data['research_summary'] = "Error generating research summary"
                meeting_data['preparation_questions'] = "Error generating preparation questions"
            
            enhanced_meetings.append(meeting_data)
        
        return jsonify({
            'keyword': keyword,
            'meetings': enhanced_meetings,
            'count': len(enhanced_meetings)
        })
        
    except Exception as e:
        print(f"Error searching meetings: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Enhanced Chrome Extension Server...")
    print("📅 Calendar Person Research Agent integrated!")
    print("🌐 Server will be available at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

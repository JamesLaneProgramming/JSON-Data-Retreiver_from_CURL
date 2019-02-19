# Canvas Integration
A simple Flask server that handles integration between the Canvas API and external endpoints.

##Setting up a development environment for canvas-integration.

To create a python development environment, you will need to install the latest version of python3 onto your machine as well as the pip3 package manager.
You can install pip through the default python3 installer, guides for installing on different operating systems can be found below:
###Windows:	
	https://vgkits.org/blog/pip3-windows-howto/
###Linux:


When a Canvas course section is 'Cross-List' into another course, the 'section_id' and 'course_id' will change. Any webhooks pointing to the original endpoint will need to be updated. This can be accomplished by creating a new section in the original course and updating any webhooks to acknowledge these changes, this is done when you are treating this section as a staging ground for students about to start a course. The second option is to create an addition section in the new course to store any students that are added after the 'Cross-List' action.

let toggleBtn = document.getElementById('toggle-btn');
let body = document.body;
let darkMode = localStorage.getItem('dark-mode');

const enableDarkMode = () =>{
   toggleBtn.classList.replace('fa-sun', 'fa-moon');
   body.classList.add('dark');
   localStorage.setItem('dark-mode', 'enabled');
}

const disableDarkMode = () =>{
   toggleBtn.classList.replace('fa-moon', 'fa-sun');
   body.classList.remove('dark');
   localStorage.setItem('dark-mode', 'disabled');
}

if(darkMode === 'enabled'){
   enableDarkMode();
}

toggleBtn.onclick = (e) =>{
   darkMode = localStorage.getItem('dark-mode');
   if(darkMode === 'disabled'){
      enableDarkMode();
   }else{
      disableDarkMode();
   }
}

let profile = document.querySelector('.header .flex .profile');

document.querySelector('#user-btn').onclick = () =>{
   profile.classList.toggle('active');
   search.classList.remove('active');
}

let search = document.querySelector('.header .flex .search-form');

document.querySelector('#search-btn').onclick = () =>{
   search.classList.toggle('active');
   profile.classList.remove('active');
}

let sideBar = document.querySelector('.side-bar');

document.querySelector('#menu-btn').onclick = () =>{
   sideBar.classList.toggle('active');
   body.classList.toggle('active');
}

document.querySelector('#close-btn').onclick = () =>{
   sideBar.classList.remove('active');
   body.classList.remove('active');
}

window.onscroll = () =>{
   profile.classList.remove('active');
   search.classList.remove('active');

   if(window.innerWidth < 1200){
      sideBar.classList.remove('active');
      body.classList.remove('active');
   }
}

function save_course(element, url, student_id, course_id){
   const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('value')
   const options = {
     'method': "POST",
     'headers': {
       'Content-type': 'application/json',
       'X-Csrftoken': csrftoken
     },
     'body': JSON.stringify({'student_id': student_id, 'course': course_id})
   }
   fetch(url, options)
   .then(function(response) {
     if (response.ok) {
       element.classList.toggle('saved')
       let span = element.querySelector('span')
       if(element.classList.contains('saved')){
         span.innerText = 'Saved'
       }
       else {
         span.innerText = 'Save course'
       }
     } else {
       console.error('Error:', response.statusText);
     }
   })
   .catch(error => console.log('Error: ', error))
 }

async function saveCourse(button, courseId) {
    try {
        const response = await fetch('/save-course/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                course: courseId
            })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            // Toggle button appearance
            button.classList.toggle('saved');
            const span = button.querySelector('span');
            span.textContent = data.saved ? 'Saved' : 'Save Course';
            
            // Update student count if we're on the tutor dashboard
            const studentCount = document.querySelector(`[data-course-id="${courseId}"] .student-count`);
            if (studentCount) {
                studentCount.textContent = data.savedCount;
            }
        } else {
            alert(data.message || 'Error saving course');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving course');
    }
}

import { Component } from '@angular/core';
import { faDashboard, faBars, faVideo, faGear } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  faDashboard = faDashboard;
  faBars = faBars;
  faVideo = faVideo;
  faGear = faGear;
}

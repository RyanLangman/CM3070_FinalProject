import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { NgbModule, NgbToastModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClientModule } from '@angular/common/http';
import { LivestreamModalComponent } from './livestream-modal/livestream-modal.component';
import { SettingsComponent } from './settings/settings.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { RecordingsComponent } from './recordings/recordings.component';
import { ConfirmDeleteRecordingModalComponent } from './confirm-delete-recording-modal/confirm-delete-recording-modal.component';
import { FormsModule } from '@angular/forms';
import { LoaderComponent } from './loader/loader.component';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { ToastGlobalComponent } from './toast-global/toast-global.component';

@NgModule({
  declarations: [
    AppComponent,
    LivestreamModalComponent,
    SettingsComponent,
    DashboardComponent,
    RecordingsComponent,
    ConfirmDeleteRecordingModalComponent,
    LoaderComponent,
    ToastGlobalComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    NgbModule,
    HttpClientModule,
    FormsModule,
    FontAwesomeModule,
    NgbToastModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
